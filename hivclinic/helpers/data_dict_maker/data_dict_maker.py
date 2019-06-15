from datetime import date
from dateutil.relativedelta import relativedelta

from sqlalchemy import and_, func, or_

import pandas as pd
from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel
import numpy as np


def calculate_age_string(date_of_birth):
    r = relativedelta(pd.to_datetime("now"), date_of_birth)
    return "{} years {} months {} days".format(r.years, r.months, r.days)


def calculate_age_year(date_of_birth):
    r = relativedelta(pd.to_datetime("now"), date_of_birth)
    return r.years


def dataDictMaker(
    dateFormat: str = None,
    joinArrayBy: str = None,
    calculateAgeAsStr: bool = False,
    convertUUID: bool = False,
):
    # columns to be converted to string
    columns_to_str = ["id"]

    # columns to be converted to iso date
    columns_to_iso_date = [
        "dateOfBirth",
        "registerDate",
        "firstVisit",
        "firstLab",
        "firstAntiHIV",
        "firstPosAntiHIV",
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

    # find first lab
    subquery_firstLab = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstLab"),
        )
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    # find first antihiv test result
    subquery_firstAntiHIV = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstAntiHIV"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(InvestigationModel.antiHIV.isnot(None))
        .subquery()
    )

    subquery_firstAntiHIVResult = (
        db.session.query(
            subquery_firstAntiHIV.c.firstAntiHIV,
            InvestigationModel.antiHIV.label("firstAntiHIVResult"),
            InvestigationModel.patientID,
        )
        .join(
            subquery_firstAntiHIV,
            and_(
                subquery_firstAntiHIV.c.firstAntiHIV
                == InvestigationModel.date,
                subquery_firstAntiHIV.c.patientID
                == InvestigationModel.patientID,
            ),
        )
        .filter(InvestigationModel.antiHIV.isnot(None))
        .subquery()
    )

    # find first positive antihiv date
    subquery_firstPosAntiHIV = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstPosAntiHIV"),
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
            subquery_firstLab.c.firstLab,
            subquery_firstAntiHIVResult.c.firstAntiHIV,
            subquery_firstAntiHIVResult.c.firstAntiHIVResult,
            subquery_firstPosAntiHIV.c.firstPosAntiHIV,
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
            subquery_firstLab, subquery_firstLab.c.patientID == PatientModel.id
        )
        .outerjoin(
            subquery_firstAntiHIVResult,
            subquery_firstAntiHIVResult.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_firstPosAntiHIV,
            subquery_firstPosAntiHIV.c.patientID == PatientModel.id,
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
                PatientModel.clinicID.isnot(None),
                subquery_firstPosAntiHIV.c.firstPosAntiHIV.isnot(None),
                subquery_initialARV.c.arvInitiationDate.isnot(None),
                subquery_currentARV.c.lastARVPrescriptionDate.isnot(None),
                subquery_lastVLResults.c.lastViralLoadDate.isnot(None),
                subquery_lastCD4Results.c.lastCD4LabDate.isnot(None),
                subquery_firstCD4Results.c.firstCD4LabDate.isnot(None),
            )
        )
        .order_by(PatientModel.clinicID)
        .statement
    )

    df = pd.read_sql(data_dict, db.session.bind)

    # find register date
    date_df = df.ix[:, ["firstVisit", "firstLab"]]
    date_df.fillna(date.max, inplace=True)

    register_date_series = date_df.apply(np.min, axis=1)
    df.insert(19, "registerDate", register_date_series)

    # calculate age
    if calculateAgeAsStr:
        age_series = df["dateOfBirth"].apply(calculate_age_string)

    else:
        age_series = df["dateOfBirth"].apply(calculate_age_year)

    df.insert(7, "Age", age_series)

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

    # replace -1 to undetectable
    df.replace(-1, "Undetectable", inplace=True)

    # add column names
    column_names = [
        "ID",
        "Clinic ID",
        "HN",
        "Government ID",
        "NAP",
        "Name",
        "Date of birth",
        "Age",
        "Sex",
        "Gender",
        "Marital status",
        "Nationality",
        "Healthcare scheme",
        "Phone number",
        "Relative's phone number",
        "Referral status",
        "Referred from",
        "Risk behaviors",
        "Patient status",
        "Number of partners",
        "Register date",
        "First visit",
        "First lab",
        "First anti-HIV testing on",
        "First anti-HIV testing result",
        "Anti-HIV positive on",
        "Start ARV on",
        "First ARV regimen",
        "Last ARV prescription",
        "Last ARV regimen",
        "Last viral load on",
        "Last viral load result",
        "First CD4 on",
        "First CD4 result",
        "First %CD4 result",
        "Last CD4 on",
        "Last CD4 result",
        "Last %CD4 result",
    ]

    df.columns = column_names

    # replace missing values to None
    df = df.where(df.notnull(), None)

    return df
