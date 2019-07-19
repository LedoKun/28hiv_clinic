from datetime import date
from dateutil.relativedelta import relativedelta

from sqlalchemy import and_, func, or_, exists

import pandas as pd
from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel
import numpy as np

import sys


def calculate_age_string(date_of_birth):
    r = relativedelta(pd.to_datetime("now"), date_of_birth)
    return "{} years {} months {} days".format(r.years, r.months, r.days)


def calculate_age_year(date_of_birth):
    r = relativedelta(pd.to_datetime("now"), date_of_birth)
    return r.years


def dataDictMaker(
    dateFormat: str = None,
    joinArrayBy: str = ",",
    calculateAgeAsStr: bool = False,
    convertUUID: bool = False,
    startDate: date = date.min,
    endDate: date = date.max,
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

    # find first visit
    subquery_firstVisit = (
        db.session.query(
            VisitModel.patientID, func.min(VisitModel.date).label("firstVisit")
        )
        .group_by(VisitModel.patientID)
        .filter(VisitModel.date.between(startDate, endDate))
        .subquery()
    )

    # find first lab
    subquery_firstLab = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstLab"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(InvestigationModel.date.between(startDate, endDate))
        .subquery()
    )

    # # find register date
    # subquery_registerDate = (
    #     db.session.query(
    #         func.min(
    #             subquery_firstVisit.c.firstVisit,
    #             subquery_firstLab.c.firstLab
    #         )
    #         .label("registerDate")
    #     )
    #     .filter(
    #         and_(

    #         )
    #     )
    # )

    # find first antihiv test result
    subquery_firstAntiHIV = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstAntiHIV"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(
            and_(
                InvestigationModel.antiHIV.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .subquery()
    )

    subquery_firstAntiHIVResult = (
        db.session.query(
            InvestigationModel.date.label("firstAntiHIV"),
            InvestigationModel.antiHIV.label("firstAntiHIVResult"),
            InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_firstAntiHIV.c.firstAntiHIV
                == InvestigationModel.date,
                subquery_firstAntiHIV.c.patientID
                == InvestigationModel.patientID,
            )
        )
        .subquery()
    )

    # find first positive antihiv date
    subquery_firstPosAntiHIV = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstPosAntiHIV"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(
            and_(
                InvestigationModel.antiHIV != "Negative",
                ~InvestigationModel.antiHIV.contains("Incon"),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
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
                func.array_length(VisitModel.arvMedications, 1) != 0,
                VisitModel.date.between(startDate, endDate),
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
        .filter(
            and_(
                subquery_arvInitiationDate.c.arvInitiationDate
                == VisitModel.date,
                subquery_arvInitiationDate.c.patientID == VisitModel.patientID,
                subquery_arvInitiationDate.c.arvInitiationDate.isnot(None),
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
                func.array_length(VisitModel.arvMedications, 1) != 0,
                VisitModel.date.between(startDate, endDate),
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
        .filter(
            and_(
                subquery_lastARVPrescriptionDate.c.lastARVPrescriptionDate
                == VisitModel.date,
                subquery_lastARVPrescriptionDate.c.patientID
                == VisitModel.patientID,
            )
        )
        .subquery()
    )

    # find last VL
    subquery_lastVLLabDate = (
        db.session.query(
            InvestigationModel.patientID,
            func.max(InvestigationModel.date).label("lastViralLoadDate"),
        )
        .group_by(InvestigationModel.patientID)
        .filter(
            and_(
                InvestigationModel.viralLoad.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .subquery()
    )

    subquery_lastVLResults = (
        db.session.query(
            subquery_lastVLLabDate.c.lastViralLoadDate,
            InvestigationModel.viralLoad.label("lastViralLoad"),
            InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_lastVLLabDate.c.lastViralLoadDate
                == InvestigationModel.date,
                subquery_lastVLLabDate.c.patientID
                == InvestigationModel.patientID,
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
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .subquery()
    )

    subquery_firstCD4Results = (
        db.session.query(
            subquery_firstCD4LabDate.c.firstCD4LabDate,
            InvestigationModel.id,
            InvestigationModel.absoluteCD4.label("firstCD4Result"),
            InvestigationModel.percentCD4.label("firstPercentCD4Result"),
            InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_firstCD4LabDate.c.firstCD4LabDate
                == InvestigationModel.date,
                subquery_firstCD4LabDate.c.patientID
                == InvestigationModel.patientID,
            )
        )
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
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .subquery()
    )

    subquery_lastCD4Results = (
        db.session.query(
            subquery_lastCD4LabDate.c.lastCD4LabDate,
            InvestigationModel.id,
            InvestigationModel.absoluteCD4.label("lastCD4Result"),
            InvestigationModel.percentCD4.label("lastPercentCD4Result"),
            InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_lastCD4LabDate.c.lastCD4LabDate
                == InvestigationModel.date,
                subquery_lastCD4LabDate.c.patientID
                == InvestigationModel.patientID,
                ~exists().where(
                    subquery_firstCD4Results.c.id == InvestigationModel.id
                ),
            )
        )
        .subquery()
    )

    # first diagnosis before or equal to ARV start date (find OI)
    subquery_unnestDxBeforeARV = (
        db.session.query(
            VisitModel.patientID,
            func.unnest(VisitModel.impression).label("unnestDxBeforeARV"),
        )
        .outerjoin(
            subquery_firstPosAntiHIV,
            subquery_firstPosAntiHIV.c.patientID == VisitModel.patientID,
        )
        .outerjoin(
            subquery_firstVisit,
            subquery_firstVisit.c.patientID == VisitModel.patientID,
        )
        .outerjoin(
            subquery_firstLab,
            subquery_firstLab.c.patientID == VisitModel.patientID,
        )
        .filter(
            and_(
                subquery_firstPosAntiHIV.c.patientID.isnot(None),
                subquery_initialARV.c.patientID.isnot(None),
                or_(
                    VisitModel.date >= subquery_firstVisit.c.firstVisit,
                    VisitModel.date >= subquery_firstLab.c.firstLab,
                ),
                VisitModel.date <= subquery_initialARV.c.arvInitiationDate,
                func.array_length(VisitModel.impression, 1) != 0,
            )
        )
        .group_by(VisitModel.patientID, "unnestDxBeforeARV")
        .subquery()
    )

    subquery_DxBeforeARV = (
        db.session.query(
            VisitModel.patientID,
            func.array_agg(
                func.distinct(subquery_unnestDxBeforeARV.c.unnestDxBeforeARV)
            ).label("DxBeforeARV"),
        )
        .filter(VisitModel.patientID == subquery_unnestDxBeforeARV.c.patientID)
        .group_by(VisitModel.patientID)
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
            PatientModel.address,
            PatientModel.healthInsurance,
            PatientModel.care,
            func.array_to_string(PatientModel.phoneNumbers, joinArrayBy),
            func.array_to_string(
                PatientModel.relativePhoneNumbers, joinArrayBy
            ),
            PatientModel.referralStatus,
            PatientModel.referredFrom,
            func.array_to_string(PatientModel.riskBehaviors, joinArrayBy),
            PatientModel.patientStatus,
            PatientModel.referredOutTo,
            subquery_numberOfPartners.c.numberOfPartners,
            subquery_firstVisit.c.firstVisit,
            subquery_firstLab.c.firstLab,
            subquery_firstAntiHIVResult.c.firstAntiHIV,
            subquery_firstAntiHIVResult.c.firstAntiHIVResult,
            subquery_firstPosAntiHIV.c.firstPosAntiHIV,
            subquery_initialARV.c.arvInitiationDate,
            func.array_to_string(
                subquery_initialARV.c.initialARV, joinArrayBy
            ),
            subquery_currentARV.c.lastARVPrescriptionDate,
            func.array_to_string(
                subquery_currentARV.c.currentARV, joinArrayBy
            ),
            subquery_lastVLResults.c.lastViralLoadDate,
            subquery_lastVLResults.c.lastViralLoad,
            subquery_firstCD4Results.c.firstCD4LabDate,
            subquery_firstCD4Results.c.firstCD4Result,
            subquery_firstCD4Results.c.firstPercentCD4Result,
            subquery_lastCD4Results.c.lastCD4LabDate,
            subquery_lastCD4Results.c.lastCD4Result,
            subquery_lastCD4Results.c.lastPercentCD4Result,
            func.array_to_string(
                subquery_DxBeforeARV.c.DxBeforeARV, joinArrayBy
            ),
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
            subquery_firstCD4Results,
            subquery_firstCD4Results.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_lastCD4Results,
            subquery_lastCD4Results.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_DxBeforeARV,
            subquery_DxBeforeARV.c.patientID == PatientModel.id,
        )
        .filter(
            and_(
                or_(
                    PatientModel.clinicID.isnot(None),
                    subquery_firstPosAntiHIV.c.firstPosAntiHIV.isnot(None),
                    subquery_initialARV.c.arvInitiationDate.isnot(None),
                    subquery_currentARV.c.lastARVPrescriptionDate.isnot(None),
                    subquery_lastVLResults.c.lastViralLoadDate.isnot(None),
                    subquery_lastCD4Results.c.lastCD4LabDate.isnot(None),
                    subquery_firstCD4Results.c.firstCD4LabDate.isnot(None),
                ),
                or_(
                    subquery_firstVisit.c.firstVisit.between(
                        startDate, endDate
                    ),
                    subquery_firstLab.c.firstLab.between(startDate, endDate),
                ),
            )
        )
        .order_by(PatientModel.clinicID)
        .order_by(PatientModel.dateOfBirth)
        .order_by(subquery_firstPosAntiHIV.c.firstPosAntiHIV)
        .statement
    )

    df = pd.read_sql(data_dict, db.session.bind)

    # find register date
    date_df = df.loc[:, ["firstVisit", "firstLab"]]
    date_df.fillna(date.max, inplace=True)

    register_date_series = date_df.apply(np.min, axis=1)
    df.insert(22, "registerDate", register_date_series)

    # convert to datetime object
    if columns_to_iso_date:
        df.loc[:, columns_to_iso_date] = pd.DataFrame(
            df.loc[:, columns_to_iso_date]
        )

    # calculate time to start ARV
    time_to_arv = (
        df["arvInitiationDate"] - df["firstPosAntiHIV"]
    ).dt.days.fillna(value=sys.maxsize)

    # numpy.inf are not considered NA values
    time_to_arv.loc[time_to_arv < 0] = 0
    time_to_arv.loc[time_to_arv == sys.maxsize] = ""

    df.insert(30, "timeToStartArv", time_to_arv)

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

    # replace -1 to undetectable
    df["lastViralLoad"].replace(-1, "Undetectable", inplace=True)

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
        "Address",
        "Healthcare scheme",
        "PCU/SCU/Registered clinic",
        "Phone number",
        "Relative's phone number",
        "Referral status",
        "Referred from",
        "Risk behaviors",
        "Patient status",
        "Referred out to",
        "Number of partners",
        "Register date",
        "First visit",
        "First lab",
        "First anti-HIV testing on",
        "First anti-HIV testing result",
        "Anti-HIV positive on",
        "Start ARV on",
        "First ARV regimen",
        "# of days to start ARV",
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
        "Diagnosis before ARV initiation",
    ]

    df.columns = column_names

    # replace missing values to None
    df = df.where(df.notnull(), None)

    return df
