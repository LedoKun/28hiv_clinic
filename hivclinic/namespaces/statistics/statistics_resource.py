from datetime import date

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_restplus import Resource
from sqlalchemy import func, and_
import pandas as pd

from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel

from . import api


@api.route("/dashboard")
class DashboardStatisticsResource(Resource):
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


@api.route("/")
class StatisticsResource(Resource):
    def queryPatientDF(self):
        # columns to be converted to string
        columns_to_str = ["id"]
        # columns to be converted to iso date
        columns_to_iso_date = [
            "dateOfBirth",
            "firstVisit",
            "ARVStartDate",
            "firstPositiveAntiHIVDate",
            "lastLVLabDate",
            "lastCD4LabDate",
            "firstCD4LabDate",
        ]

        # find first visit
        subquery_firstVisit = (
            db.session.query(
                VisitModel.patientID,
                func.min(VisitModel.date).label("firstVisit"),
            )
            .group_by(VisitModel.patientID)
            .subquery()
        )

        # find arv start date
        subquery_ARVStartDate = (
            db.session.query(
                VisitModel.patientID,
                func.min(VisitModel.date).label("ARVStartDate"),
            )
            .filter(VisitModel.arvMedications.isnot(None))
            .group_by(VisitModel.patientID)
            .subquery()
        )

        # find first antihiv date
        subquery_firstPositiveAntiHIVDate = (
            db.session.query(
                InvestigationModel.patientID,
                func.min(InvestigationModel.date).label(
                    "firstPositiveAntiHIVDate"
                ),
            )
            .filter(InvestigationModel.antiHIV == "Positive")
            .group_by(InvestigationModel.patientID)
            .subquery()
        )

        # find number of partners
        subquery_numberOfPartners = (
            db.session.query(
                PartnerModel.patientID,
                func.count(PartnerModel.id).label("numberOfPartners"),
            )
            .group_by(PartnerModel.patientID)
            .subquery()
        )

        # find last VL date
        subquery_lastVLLabDate = (
            db.session.query(
                InvestigationModel.patientID,
                func.max(VisitModel.date).label("lastLVLabDate"),
            )
            .group_by(InvestigationModel.patientID)
            .filter(InvestigationModel.viralLoad.isnot(None))
            .subquery()
        )

        # find last VL result and date
        subquery_lastVLResults = (
            db.session.query(
                InvestigationModel.date.label("lastLVLabDate"),
                InvestigationModel.viralLoad,
                InvestigationModel.patientID,
            )
            .outerjoin(
                subquery_lastVLLabDate,
                and_(
                    subquery_lastVLLabDate.c.patientID
                    == InvestigationModel.patientID,
                    subquery_lastVLLabDate.c.lastLVLabDate
                    == InvestigationModel.date,
                ),
            )
            .filter(InvestigationModel.viralLoad.isnot(None))
            .subquery()
        )

        # find last CD4 date
        subquery_lastCD4LabDate = (
            db.session.query(
                InvestigationModel.patientID,
                func.max(VisitModel.date).label("lastCD4LabDate"),
            )
            .group_by(InvestigationModel.patientID)
            .filter(InvestigationModel.absoluteCD4.isnot(None))
            .subquery()
        )

        # find last CD4, %CD4 results and date
        subquery_lastCD4Results = (
            db.session.query(
                InvestigationModel.date.label("lastCD4LabDate"),
                InvestigationModel.absoluteCD4.label("lastCD4Result"),
                InvestigationModel.percentCD4.label("lastPercentCD4Result"),
                InvestigationModel.patientID,
            )
            .outerjoin(
                subquery_lastCD4LabDate,
                and_(
                    subquery_lastCD4LabDate.c.patientID
                    == InvestigationModel.patientID,
                    subquery_lastCD4LabDate.c.lastCD4LabDate
                    == InvestigationModel.date,
                ),
            )
            .filter(InvestigationModel.absoluteCD4.isnot(None))
            .filter(InvestigationModel.percentCD4.isnot(None))
            .subquery()
        )

        # find first CD4 date
        subquery_firstCD4LabDate = (
            db.session.query(
                InvestigationModel.patientID,
                func.max(VisitModel.date).label("firstCD4LabDate"),
            )
            .group_by(InvestigationModel.patientID)
            .filter(InvestigationModel.absoluteCD4.isnot(None))
            .subquery()
        )

        # find first CD4, %CD4 results and date
        subquery_firstCD4Results = (
            db.session.query(
                InvestigationModel.date.label("firstCD4LabDate"),
                InvestigationModel.absoluteCD4.label("firstCD4Result"),
                InvestigationModel.percentCD4.label("firstPercentCD4Result"),
                InvestigationModel.patientID,
            )
            .outerjoin(
                subquery_firstCD4LabDate,
                and_(
                    subquery_firstCD4LabDate.c.patientID
                    == InvestigationModel.patientID,
                    subquery_firstCD4LabDate.c.firstCD4LabDate
                    == InvestigationModel.date,
                ),
            )
            .filter(InvestigationModel.absoluteCD4.isnot(None))
            .filter(InvestigationModel.percentCD4.isnot(None))
            .subquery()
        )

        # construct data dict
        data_dict = (
            db.session.query(
                PatientModel.id,
                PatientModel.clinicID,
                PatientModel.hn,
                PatientModel.governmentID,
                PatientModel.napID,
                PatientModel.name,
                PatientModel.dateOfBirth,
                PatientModel.sex,
                PatientModel.gender,
                PatientModel.maritalStatus,
                PatientModel.nationality,
                PatientModel.healthInsurance,
                PatientModel.phoneNumbers,
                PatientModel.relativePhoneNumbers,
                PatientModel.referralStatus,
                PatientModel.referredFrom,
                PatientModel.riskBehaviors,
                PatientModel.patientStatus,
                subquery_firstVisit.c.firstVisit,
                subquery_ARVStartDate.c.ARVStartDate,
                subquery_firstPositiveAntiHIVDate.c.firstPositiveAntiHIVDate,
                subquery_numberOfPartners.c.numberOfPartners,
                subquery_lastVLResults.c.lastLVLabDate,
                subquery_lastVLResults.c.viralLoad,
                subquery_lastCD4Results.c.lastCD4LabDate,
                subquery_lastCD4Results.c.lastCD4Result,
                subquery_lastCD4Results.c.lastPercentCD4Result,
                subquery_firstCD4Results.c.firstCD4LabDate,
                subquery_firstCD4Results.c.firstCD4Result,
                subquery_firstCD4Results.c.firstPercentCD4Result,
            )
            .outerjoin(
                subquery_firstVisit,
                subquery_firstVisit.c.patientID == PatientModel.id,
            )
            .outerjoin(
                subquery_ARVStartDate,
                subquery_ARVStartDate.c.patientID == PatientModel.id,
            )
            .outerjoin(
                subquery_firstPositiveAntiHIVDate,
                subquery_firstPositiveAntiHIVDate.c.patientID
                == PatientModel.id,
            )
            .outerjoin(
                subquery_numberOfPartners,
                subquery_numberOfPartners.c.patientID == PatientModel.id,
            )
            .outerjoin(
                subquery_lastVLResults,
                subquery_lastVLResults.c.patientID == PatientModel.id,
            )
            .outerjoin(
                subquery_lastCD4Results,
                subquery_lastCD4Results.c.patientID == PatientModel.id,
            )
            .outerjoin(
                subquery_firstCD4Results,
                subquery_firstCD4Results.c.patientID == PatientModel.id,
            )
            # .filter(PatientModel.clinicID.isnot(None))
            .statement
        )

        df = pd.read_sql(data_dict, db.session.bind)

        # convert to str
        df[columns_to_str] = df[columns_to_str].astype(str, errors="ignore")

        # convert to iso date
        df[columns_to_iso_date] = df[columns_to_iso_date].applymap(
            lambda date_obj: date_obj.strftime("%Y-%m-%d")
            if isinstance(date_obj, date)
            else date_obj
        )

        return df

    def get(self):
        """Provide Clinic Statistics"""
        patientDataDict_df = self.queryPatientDF()

        return patientDataDict_df.to_dict("records")

