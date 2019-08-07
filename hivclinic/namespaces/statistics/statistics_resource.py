from datetime import date, datetime
from io import BytesIO

from dateutil.relativedelta import relativedelta
from flask import current_app, send_file
from flask_restplus import Resource
from sqlalchemy import func
from webargs import fields
from webargs.flaskparser import use_args

import pandas as pd
import numpy as np
from hivclinic import db
from hivclinic.helpers.data_dict_maker.data_dict_maker import dataDictMaker
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel

from . import api


@api.route("/dashboard")
class DashboardStatisticsResource(Resource):
    @api.doc("generate_statistics_for_dashboard")
    @staticmethod
    def count_patient():
        # count total (registered patients)
        patient_count_sql = (
            db.session.query(PatientModel.id)
            .filter(PatientModel.clinicID.isnot(None))
            .statement.with_only_columns([func.count()])
            .order_by(None)
        )
        patient_count = db.engine.execute(patient_count_sql).scalar() or 0

        return patient_count

    @staticmethod
    def count_hc_scheme():
        # count unique healthcare scheme
        healthcare_scheme_count = (
            db.session.query(
                PatientModel.healthInsurance,
                func.count(PatientModel.healthInsurance),
            )
            .filter(PatientModel.clinicID.isnot(None))
            .group_by(PatientModel.healthInsurance)
            .all()
        )

        simplified_scheme_count = {"pay": 0, "uc": 0, "sss": 0, "gov": 0}

        for item in healthcare_scheme_count:
            if item[0] == "ชำระเงินเอง" or item[0] == "สถานะคนต่างด้าว":
                simplified_scheme_count["pay"] += int(item[1])

            elif "สิทธิเบิกกรมบัญชีกลาง" in item[0]:
                simplified_scheme_count["gov"] += int(item[1])

            elif "สิทธิประกันสังคม" in item[0]:
                simplified_scheme_count["sss"] += int(item[1])

            else:
                simplified_scheme_count["uc"] += int(item[1])

        return simplified_scheme_count

    @staticmethod
    def count_examined_patient():
        # examined patient count
        examined_count_sql = (
            db.session.query(VisitModel.id)
            .join(PatientModel)
            .filter(VisitModel.date == date.today())
            .filter(PatientModel.clinicID.isnot(None))
            .statement.with_only_columns([func.count()])
            .order_by(None)
        )
        examined_count = db.engine.execute(examined_count_sql).scalar() or 0

        return examined_count

    @staticmethod
    def count_new_patient_that_examined():
        # count new patients for today
        new_patient_count_sql = (
            db.session.query(VisitModel.patientID)
            .join(PatientModel)
            .filter(PatientModel.clinicID.isnot(None))
            .filter(VisitModel.date == date.today())
            .group_by(VisitModel.patientID)
            .having(db.func.count(VisitModel.patientID) > 1)
            .statement.with_only_columns([func.count()])
            .order_by(None)
        )
        new_patient_count = (
            db.engine.execute(new_patient_count_sql).scalar() or 0
        )

        return new_patient_count

    @staticmethod
    def overdue_vl():
        overdue_date = date.today() - relativedelta(
            months=current_app.config["OVERDUE_VL_MONTHS"]
        )

        last_lab_subquery = (
            db.session.query(
                InvestigationModel.patientID,
                func.max(InvestigationModel.date).label("last_lab_date"),
            )
            .filter(InvestigationModel.viralLoad.isnot(None))
            .group_by(InvestigationModel.patientID)
            .subquery()
        )

        patients = (
            db.session.query(
                PatientModel.id,
                PatientModel.name,
                PatientModel.hn,
                PatientModel.clinicID,
                last_lab_subquery.c.last_lab_date,
            )
            .join(
                last_lab_subquery,
                last_lab_subquery.c.patientID == PatientModel.id,
            )
            .filter(PatientModel.clinicID.isnot(None))
            .filter(last_lab_subquery.c.last_lab_date <= overdue_date)
            .order_by(last_lab_subquery.c.last_lab_date.desc())
            .all()
        )

        # serialize query
        overdue_vl = []
        for item in patients:
            overdue_vl.append(
                {
                    "last_lab_date": item.last_lab_date.strftime("%Y-%m-%d"),
                    "id": str(item.id),
                    "hn": item.hn,
                    "name": item.name,
                    "clinicID": item.clinicID,
                }
            )

        return overdue_vl

    @staticmethod
    def overdue_fu():
        overdue_date = date.today() - relativedelta(
            months=current_app.config["OVERDUE_FU_MONTHS"]
        )

        last_fu_subquery = (
            db.session.query(
                VisitModel.patientID,
                func.max(VisitModel.date).label("last_fu_date"),
            )
            .group_by(VisitModel.patientID)
            .subquery()
        )

        patients = (
            db.session.query(
                PatientModel.id,
                PatientModel.name,
                PatientModel.hn,
                PatientModel.clinicID,
                last_fu_subquery.c.last_fu_date,
            )
            .join(
                last_fu_subquery,
                last_fu_subquery.c.patientID == PatientModel.id,
            )
            .filter(PatientModel.clinicID.isnot(None))
            .filter(last_fu_subquery.c.last_fu_date <= overdue_date)
            .order_by(last_fu_subquery.c.last_fu_date.desc())
            .all()
        )

        # serialize query
        overdue_fu = []
        for item in patients:
            overdue_fu.append(
                {
                    "last_fu_date": item.last_fu_date.strftime("%Y-%m-%d"),
                    "id": str(item.id),
                    "hn": item.hn,
                    "name": item.name,
                    "clinicID": item.clinicID,
                }
            )

        return overdue_fu

    @api.doc("provide_dashboard_statistics")
    def get(self):
        """Provide Dashboard Statistics"""

        return {
            "patientCount": self.count_patient(),
            "healthcareSchemeCount": self.count_hc_scheme(),
            "examinedCount": self.count_examined_patient(),
            "newPatientCount": self.count_new_patient_that_examined(),
            "overdueVL": self.overdue_vl(),
            "overdueFU": self.overdue_fu(),
        }


@api.route("/data_dict")
class DataDictResource(Resource):
    @api.doc("generate_patient_data_dict")
    @use_args({"as_file": fields.Boolean(missing=False)})
    def get(self, args):
        """Provide Clinic Statistics"""
        patientDataDict_df = dataDictMaker(
            dateFormat="%d-%m-%Y",
            joinArrayBy=", ",
            calculateAgeAsStr=True,
            convertUUID=True,
        )

        if args["as_file"]:
            # create an output stream
            output = BytesIO()

            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                patientDataDict_df.to_excel(writer, sheet_name="DataDict")

            output.seek(0)

            return send_file(
                output,
                attachment_filename="data_dict.xlsx",
                as_attachment=True,
            )

        else:
            table_data = {
                "colHeaders": list(patientDataDict_df.columns),
                "data": patientDataDict_df.values.tolist(),
            }

            return table_data, 200


@api.route("/overview")
class OverviewResource(Resource):
    @staticmethod
    def getNumberOfNewPatientsStats(df, column_name):
        df = df.loc[:, [column_name]]

        count_data = (
            df.groupby(
                [
                    df[column_name].dt.year.rename("Year"),
                    df[column_name].dt.month.rename("Month"),
                ]
            )
            .agg({"count"})
            .sort_index()
        )

        count_data.columns = ["New"]
        count_data["Total"] = count_data.cumsum()

        return count_data.T

    @staticmethod
    def getNumberStats(df, db_column_name, count_column_name):
        count_data = (
            df.groupby(
                [
                    df[db_column_name].dt.year.rename("Year"),
                    df[db_column_name].dt.month.rename("Month"),
                ]
            )
            .agg({"count"})
            .sort_index()
        )

        count_data.columns = [count_column_name]

        return count_data.T

    @staticmethod
    def getWeeklyHeatmap(df, column_name, count_column_name):
        df = df.loc[:, [column_name]]

        count_data = (
            df.groupby([df[column_name].dt.weekday.rename("Day")])
            .agg({"count"})
            .sort_index()
        )

        count_data.columns = [count_column_name]
        df[column_name] = df[column_name].dt.weekday_name

        return count_data.T

    @staticmethod
    def getNationalityStats(df):
        df = df.loc[:, ["ID", "Nationality", "Healthcare scheme"]]

        count_data = (
            df.groupby(
                [df.loc[:, "Nationality"], df.loc[:, "Healthcare scheme"]]
            )
            .agg({"count"})
            .sort_index()
        )

        count_data.columns = ["Cases"]

        return count_data

    @staticmethod
    def calculate_age(born):
        if isinstance(born, date):
            today = date.today()
            age = (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )

            return age

        else:
            return None

    @staticmethod
    def getAgeCrossedTable(df, column_names=[], no_data_as="No Data"):
        bins = np.arange(0, 1000, 10)
        groupby_columns = [pd.cut(df.Age, bins)] + column_names

        df.drop(["Age"], axis=1, inplace=True)
        df.fillna(no_data_as, inplace=True)

        count_data = df.groupby(groupby_columns).agg({"count"}).sort_index()

        # rename columns
        count_data.columns = ["#"]

        return count_data

    @staticmethod
    def grouppedTable(df, column_names=[], no_data_as="No Data"):
        df.fillna(no_data_as, inplace=True)
        count_data = df.groupby(column_names).agg({"count"}).sort_index()

        # rename columns
        count_data.columns = ["#"]

        count_data.sort_index(inplace=True)

        return count_data

    @staticmethod
    def getCD4CrossedTable(
        df, column_names=[], cd4_column_name=None, no_data_as="No Data"
    ):
        df.dropna(axis="index", subset=[cd4_column_name], inplace=True)

        bins = [-1, 200, 350, 5000]
        labels = ["[0, 200]", "(200, 350]", "(350, ∞)"]

        groupby_columns = [
            pd.cut(df.loc[:, cd4_column_name], bins=bins, labels=labels)
        ] + column_names

        df.drop([cd4_column_name], axis=1, inplace=True)
        df.fillna(no_data_as, inplace=True)

        count_data = df.groupby(groupby_columns).agg({"count"}).sort_index()

        # rename columns
        count_data.columns = ["#"]

        return count_data

    @staticmethod
    def getVLTable(
        df, column_names=[], vl_column_name=None, no_data_as="No Data"
    ):
        df.dropna(axis="index", subset=[vl_column_name], inplace=True)
        df.replace("Undetectable", -1, inplace=True)
        df[vl_column_name] = df[vl_column_name].astype(int)

        bins = [-2, 0, 200, 1000, 9999999]
        labels = ["Undetectable", "VL ≤ 200", "VL ≤ 1000", "VL > 1000"]

        groupby_columns = [
            pd.cut(df.loc[:, vl_column_name], bins=bins, labels=labels)
        ] + column_names

        df.drop([vl_column_name], axis=1, inplace=True)
        df.fillna(no_data_as, inplace=True)

        count_data = df.groupby(groupby_columns).agg({"count"}).sort_index()

        # rename columns
        count_data.columns = ["#"]

        return count_data

    @api.doc("generate_overview_statistics")
    @use_args(
        {
            "startDate": fields.Date(missing=date.min),
            "endDate": fields.Date(missing=date.max),
        }
    )
    def get(self, args):
        """Provide Clinic's Overview Statistics"""
        joinArrayBy = ","
        patientDataDict_df = dataDictMaker(
            joinArrayBy=joinArrayBy,
            calculateAgeAsStr=True,
            convertUUID=True,
            startDate=args["startDate"],
            endDate=args["endDate"],
        )

        # recalculate age as relative time
        patientDataDict_df["Date of birth"] = pd.to_datetime(
            patientDataDict_df["Date of birth"], errors="ignore", format='%d-%m-%Y'
        )

        # calculate age
        patientDataDict_df["Age"] = patientDataDict_df["Date of birth"].apply(
            self.calculate_age
        )

        col_name = "Register date"
        patientDataDict_df[col_name] = pd.to_datetime(
            patientDataDict_df[col_name], errors="coerce", infer_datetime_format=True
        )

        # thais and nonthais
        thais_df = patientDataDict_df.where(
            patientDataDict_df["Nationality"] == "ไทย"
        )

        nonthais_df = patientDataDict_df.where(
            patientDataDict_df["Nationality"] != "ไทย"
        )

        # visits df
        patient_visit_df = pd.read_sql(
            db.session.query(VisitModel.date)
            .filter(
                VisitModel.date.between(args["startDate"], args["endDate"])
            )
            .statement,
            db.session.bind,
        )

        patient_visit_df["date"] = pd.to_datetime(
            patient_visit_df["date"], errors="coerce", infer_datetime_format=True
        )

        # ix df
        patient_ix_df = pd.read_sql(
            db.session.query(InvestigationModel.date)
            .filter(
                InvestigationModel.date.between(
                    args["startDate"], args["endDate"]
                )
            )
            .statement,
            db.session.bind,
        )

        patient_ix_df["date"] = pd.to_datetime(
            patient_ix_df["date"], errors="coerce", infer_datetime_format=True
        )

        # count new patients
        patient_count = self.getNumberOfNewPatientsStats(
            patientDataDict_df, "Register date"
        )

        # count visits
        visits_count = self.getNumberStats(
            df=patient_visit_df,
            db_column_name="date",
            count_column_name="Visits",
        )

        # count ix
        ix_count = self.getNumberStats(
            df=patient_ix_df,
            db_column_name="date",
            count_column_name="Investigations",
        )

        # weekly new cases heatmap
        weekly_new_cases_heatmap = self.getWeeklyHeatmap(
            df=patientDataDict_df,
            column_name=col_name,
            count_column_name="New Cases",
        )

        # weekly visits heatmap
        weekly_visits_heatmap = self.getWeeklyHeatmap(
            df=patient_visit_df, column_name="date", count_column_name="Visits"
        )

        # count nationality
        patient_nationality = self.getNationalityStats(patientDataDict_df)

        # patient_age_sex_gender
        patient_age_sex_gender = self.getAgeCrossedTable(
            df=patientDataDict_df.loc[:, ["ID", "Age", "Sex", "Gender"]],
            column_names=["Sex", "Gender"],
        )

        # Age/Nationality/Referral Status/Referred From
        patient_age_nat_referral = self.getAgeCrossedTable(
            df=patientDataDict_df.loc[
                :,
                [
                    "ID",
                    "Age",
                    "Nationality",
                    "Referral status",
                    "Referred from",
                ],
            ],
            column_names=["Nationality", "Referral status", "Referred from"],
            no_data_as="N/A",
        )

        # Age/Nationality/Patient Status/Referred Out To
        patient_age_nat_referral_out = self.getAgeCrossedTable(
            df=patientDataDict_df.loc[
                :,
                [
                    "ID",
                    "Age",
                    "Nationality",
                    "Patient status",
                    "Referred out to",
                ],
            ],
            column_names=["Nationality", "Patient status", "Referred out to"],
            no_data_as="N/A",
        )

        # Age/Sex/Gender/Risk Behaviors
        patient_age_sex_gender_risk = self.getAgeCrossedTable(
            df=patientDataDict_df.loc[
                :, ["ID", "Age", "Sex", "Gender", "Risk behaviors"]
            ],
            column_names=["Sex", "Gender", "Risk behaviors"],
        )

        # Other diagnosis before ARV initiation
        column_name = "Other diagnosis before ARV initiation"

        dx_df = patientDataDict_df.loc[
            :, ["ID", column_name]
        ]
        
        dx_df[column_name] = (
            dx_df[column_name]
            .apply(lambda data_string: data_string.split(joinArrayBy) if isinstance(data_string, str) else data_string)
        )

        dx_df = dx_df.explode(column_name)

        patient_other_dx = self.grouppedTable(
            df=dx_df.loc[
                :, ["ID", column_name]
            ],
            column_names=[column_name],
            no_data_as="N/A",
        )

        # Current ARV Regimen
        patient_current_arv = self.grouppedTable(
            df=patientDataDict_df.loc[
                :, ["ID", "Last ARV regimen"]
            ],
            column_names=["Last ARV regimen"],
            no_data_as="N/A",
        )

        # initial cd4 by sex & gender
        init_cd4_sex_gender = self.getCD4CrossedTable(
            df=patientDataDict_df.loc[
                :, ["ID", "First CD4 result", "Sex", "Gender"]
            ],
            cd4_column_name="First CD4 result",
            column_names=["Sex", "Gender"],
        )

        # last cd4 by sex & gender
        last_cd4_sex_gender = self.getCD4CrossedTable(
            df=patientDataDict_df.loc[
                :, ["ID", "Last CD4 result", "Sex", "Gender"]
            ],
            cd4_column_name="Last CD4 result",
            column_names=["Sex", "Gender"],
        )

        # initial cd4 by sex & gender for Thais
        init_cd4_sex_gender_thais = self.getCD4CrossedTable(
            df=thais_df.loc[:, ["ID", "First CD4 result", "Sex", "Gender"]],
            cd4_column_name="First CD4 result",
            column_names=["Sex", "Gender"],
        )

        # last cd4 by sex & gender for Thais
        last_cd4_sex_gender_thais = self.getCD4CrossedTable(
            df=thais_df.loc[:, ["ID", "Last CD4 result", "Sex", "Gender"]],
            cd4_column_name="Last CD4 result",
            column_names=["Sex", "Gender"],
        )

        # initial cd4 by sex & gender for non-thais
        init_cd4_sex_gender_nonthais = self.getCD4CrossedTable(
            df=nonthais_df.loc[:, ["ID", "First CD4 result", "Sex", "Gender"]],
            cd4_column_name="First CD4 result",
            column_names=["Sex", "Gender"],
        )

        # last cd4 by sex & gender for non-thais
        last_cd4_sex_gender_nonthais = self.getCD4CrossedTable(
            df=nonthais_df.loc[:, ["ID", "Last CD4 result", "Sex", "Gender"]],
            cd4_column_name="Last CD4 result",
            column_names=["Sex", "Gender"],
        )

        # last VL
        last_vl = self.getVLTable(
            df=patientDataDict_df.loc[:, ["ID", "Last viral load result"]],
            vl_column_name="Last viral load result",
            column_names=[],
        )

        return {
            "patientCount": patient_count.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "visitsCount": visits_count.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "ixCount": ix_count.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "newCasesHeatMap": weekly_new_cases_heatmap.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "visitHeatMap": weekly_visits_heatmap.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientNationality": patient_nationality.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientAgeSexGender": patient_age_sex_gender.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientAgeNatRefferIn": patient_age_nat_referral.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientAgeNatRefferOut": patient_age_nat_referral_out.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientAgeSexGenderRisk": patient_age_sex_gender_risk.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patienOtherDx": patient_other_dx.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "patientCurrentARV": patient_current_arv.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "initCD4SexGender": init_cd4_sex_gender.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "lastCD4SexGender": last_cd4_sex_gender.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "initCD4SexGenderThais": init_cd4_sex_gender_thais.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "lastCD4SexGenderThais": last_cd4_sex_gender_thais.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "initCD4SexGenderNonThais": init_cd4_sex_gender_nonthais.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "lastCD4SexGenderNonThais": last_cd4_sex_gender_nonthais.to_html(
                escape=True, bold_rows=False, border=0
            ),
            "lastVL": last_vl.to_html(escape=True, bold_rows=False, border=0),
        }
