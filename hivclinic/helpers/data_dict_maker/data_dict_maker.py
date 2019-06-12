from datetime import date
from dateutil.relativedelta import relativedelta

from sqlalchemy import and_, func, or_

import pandas as pd
from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel


def calculate_age_string(date_of_birth):
    r = relativedelta(pd.to_datetime('now'), date_of_birth) 
    return '{} years {} months {} days'.format(r.years, r.months, r.days)


def calculate_age_year(date_of_birth):
    r = relativedelta(pd.to_datetime('now'), date_of_birth) 
    return r.years


def dataDictMaker(
    dateFormat: str = None,
    joinArrayBy: str = None,
    calculateAgeAsStr: bool = False,
    convertUUID: bool = False
):
    # columns to be converted to string
    columns_to_str = ["id"]

    # columns to be converted to iso date
    columns_to_iso_date = [
        "dateOfBirth",
        "firstVisit",
        "firstPositiveAntiHIVDate",
        "arvInitiationDate",
        "lastARVPrescriptionDate",
        "firstCD4LabDate",
        "lastCD4LabDate",
        "lastViralLoadDate",
    ]

    # array columns to be converted to string
    columns_to_join = [
        "phoneNumbers",
        "relativePhoneNumbers",
        "riskBehaviors",
        "initialARV",
        "currentARV",
    ]

    # find first visit
    subquery_firstVisit = (
        db.session.query(
            VisitModel.patientID, func.min(VisitModel.date).label("firstVisit")
        )
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
        .group_by(InvestigationModel.patientID)
        .filter(InvestigationModel.antiHIV == "Positive")
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

    # find initial ARV
    subquery_arvInitiationDate = (
        db.session.query(
            VisitModel.patientID,
            func.min(VisitModel.date).label("arvInitiationDate"),
        )
        .group_by(VisitModel.patientID)
        .filter(
            and_(
                VisitModel.arvMedications.isnot(None),
                VisitModel.arvMedications != [],
            )
        )
        .subquery()
    )

    subquery_initialARV = (
        db.session.query(
            subquery_arvInitiationDate.c.arvInitiationDate,
            VisitModel.arvMedications.label("initialARV"),
            VisitModel.patientID,
        )
        .join(
            subquery_arvInitiationDate,
            and_(
                subquery_arvInitiationDate.c.arvInitiationDate
                == VisitModel.date,
                subquery_arvInitiationDate.c.patientID == VisitModel.patientID,
            ),
        )
        .filter(
            and_(
                VisitModel.arvMedications.isnot(None),
                VisitModel.arvMedications != [],
            )
        )
        .subquery()
    )

    # find last/current ARV regimen
    subquery_lastARVPrescriptionDate = (
        db.session.query(
            VisitModel.patientID,
            func.max(VisitModel.date).label("lastARVPrescriptionDate"),
        )
        .group_by(VisitModel.patientID)
        .filter(
            and_(
                VisitModel.arvMedications.isnot(None),
                VisitModel.arvMedications != [],
            )
        )
        .subquery()
    )

    subquery_currentARV = (
        db.session.query(
            subquery_lastARVPrescriptionDate.c.lastARVPrescriptionDate,
            VisitModel.arvMedications.label("currentARV"),
            VisitModel.patientID,
        )
        .join(
            subquery_lastARVPrescriptionDate,
            and_(
                subquery_lastARVPrescriptionDate.c.lastARVPrescriptionDate
                == VisitModel.date,
                subquery_lastARVPrescriptionDate.c.patientID
                == VisitModel.patientID,
            ),
        )
        .filter(
            and_(
                VisitModel.arvMedications.isnot(None),
                VisitModel.arvMedications != [],
            )
        )
        .subquery()
    )

    # find first VL
    subquery_lastVLLabDate = (
        db.session.query(
            InvestigationModel.patientID,
            func.max(InvestigationModel.date).label("lastViralLoadDate"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(InvestigationModel.viralLoad.isnot(None))
        .subquery()
    )

    subquery_lastVLResults = (
        db.session.query(
            subquery_lastVLLabDate.c.lastViralLoadDate,
            InvestigationModel.viralLoad.label("lastViralLoad"),
            InvestigationModel.patientID,
        )
        .join(
            subquery_lastVLLabDate,
            and_(
                subquery_lastVLLabDate.c.lastViralLoadDate
                == InvestigationModel.date,
                subquery_lastVLLabDate.c.patientID
                == InvestigationModel.patientID,
            ),
        )
        .filter(InvestigationModel.viralLoad.isnot(None))
        .subquery()
    )

    # find last CD4
    subquery_lastCD4LabDate = (
        db.session.query(
            InvestigationModel.patientID,
            func.max(InvestigationModel.date).label("lastCD4LabDate"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.percentCD4.isnot(None),
            )
        )
        .subquery()
    )

    subquery_lastCD4Results = (
        db.session.query(
            subquery_lastCD4LabDate.c.lastCD4LabDate,
            InvestigationModel.absoluteCD4.label("lastCD4Result"),
            InvestigationModel.percentCD4.label("lastPercentCD4Result"),
            InvestigationModel.patientID,
        )
        .join(
            subquery_lastCD4LabDate,
            and_(
                subquery_lastCD4LabDate.c.lastCD4LabDate
                == InvestigationModel.date,
                subquery_lastCD4LabDate.c.patientID
                == InvestigationModel.patientID,
            ),
        )
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.percentCD4.isnot(None),
            )
        )
        .subquery()
    )

    # find first CD4
    subquery_firstCD4LabDate = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstCD4LabDate"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.percentCD4.isnot(None),
            )
        )
        .subquery()
    )

    subquery_firstCD4Results = (
        db.session.query(
            subquery_firstCD4LabDate.c.firstCD4LabDate,
            InvestigationModel.absoluteCD4.label("firstCD4Result"),
            InvestigationModel.percentCD4.label("firstPercentCD4Result"),
            InvestigationModel.patientID,
        )
        .join(
            subquery_firstCD4LabDate,
            and_(
                subquery_firstCD4LabDate.c.firstCD4LabDate
                == InvestigationModel.date,
                subquery_firstCD4LabDate.c.patientID
                == InvestigationModel.patientID,
            ),
        )
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.percentCD4.isnot(None),
            )
        )
        .subquery()
    )

    # construct data_dict
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
            subquery_numberOfPartners.c.numberOfPartners,
            subquery_firstVisit.c.firstVisit,
            subquery_firstPositiveAntiHIVDate.c.firstPositiveAntiHIVDate,
            subquery_initialARV.c.arvInitiationDate,
            subquery_initialARV.c.initialARV,
            subquery_currentARV.c.lastARVPrescriptionDate,
            subquery_currentARV.c.currentARV,
            subquery_lastVLResults.c.lastViralLoadDate,
            subquery_lastVLResults.c.lastViralLoad,
            subquery_lastCD4Results.c.lastCD4LabDate,
            subquery_lastCD4Results.c.lastCD4Result,
            subquery_lastCD4Results.c.lastPercentCD4Result,
            subquery_firstCD4Results.c.firstCD4LabDate,
            subquery_firstCD4Results.c.firstCD4Result,
            subquery_firstCD4Results.c.firstPercentCD4Result,
        )
        .outerjoin(
            subquery_numberOfPartners,
            subquery_numberOfPartners.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_firstVisit,
            subquery_firstVisit.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_firstPositiveAntiHIVDate,
            subquery_firstPositiveAntiHIVDate.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_initialARV,
            subquery_initialARV.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_currentARV,
            subquery_currentARV.c.patientID == PatientModel.id,
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
        .filter(
            or_(
                subquery_firstPositiveAntiHIVDate.c.firstPositiveAntiHIVDate.isnot(
                    None
                ),
                subquery_initialARV.c.arvInitiationDate.isnot(None),
            )
        )
        .statement
    )

    df = pd.read_sql(data_dict, db.session.bind)

    # calculate age
    if calculateAgeAsStr:
        age_df = df["dateOfBirth"].apply(calculate_age_string)
        

    else:
        age_df = df["dateOfBirth"].apply(calculate_age_year)

    age_list = age_df.values.tolist()
    df.insert(7, "Age", age_list) 

    # convert to str
    if convertUUID:
        df[columns_to_str] = df[columns_to_str].astype(str, errors="ignore")

    # convert to iso date
    if dateFormat:
        df[columns_to_iso_date] = df[columns_to_iso_date].applymap(
            lambda date_obj: date_obj.strftime("%d-%m-%Y")
            if isinstance(date_obj, date)
            else date_obj
        )

    # convert to string
    if joinArrayBy:
        df[columns_to_join] = df[columns_to_join].applymap(
            lambda list_obj: joinArrayBy.join(list_obj)
            if isinstance(list_obj, (list, tuple))
            else list_obj
        )

    return df
