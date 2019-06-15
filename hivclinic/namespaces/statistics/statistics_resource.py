from datetime import date
from io import BytesIO

from dateutil.relativedelta import relativedelta
from flask import current_app, send_file
from flask_restplus import Resource
from sqlalchemy import func
from webargs import fields
from webargs.flaskparser import use_args

import pandas as pd
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
            convertUUID=True
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
                "data": patientDataDict_df.values.tolist()
            }

            return table_data, 200
