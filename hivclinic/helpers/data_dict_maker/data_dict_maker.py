from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import Unicode, Float, and_, case, func, or_
from sqlalchemy.sql.expression import cast

from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel


def calculate_age_string(date_of_birth):
    r = relativedelta(pd.to_chartime("now"), date_of_birth)
    return "{} years {} months {} days".format(r.years, r.months, r.days)


def calculate_age_year(date_of_birth):
    r = relativedelta(pd.to_chartime("now"), date_of_birth)
    return r.years


def dataDictMaker(
    dateFormat: str = None,
    joinArrayBy: str = ",",
    calculateAgeAsStr: bool = False,
    convertUUID: bool = False,
    startDate: date = date.min,
    endDate: date = date.max,
    asArray: bool = False,
):
    # find first visit
    subquery_firstVisit = (
        db.session.query(
            VisitModel.patientID, func.min(VisitModel.date).label("firstVisit")
        )
        .filter(VisitModel.date.between(startDate, endDate))
        .group_by(VisitModel.patientID)
        .subquery()
    )

    # find first lab
    subquery_firstLab = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstLab"),
        )
        .filter(InvestigationModel.date.between(startDate, endDate))
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    # find register date
    subquery_registerDate = (
        db.session.query(
            PatientModel.id.label("patientID"),
            func.least(
                func.coalesce(subquery_firstVisit.c.firstVisit, date.max),
                func.coalesce(subquery_firstLab.c.firstLab, date.max),
            ).label("registerDate"),
        )
        .outerjoin(
            subquery_firstVisit,
            subquery_firstVisit.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_firstLab, subquery_firstLab.c.patientID == PatientModel.id
        )
        .filter(
            or_(
                subquery_firstVisit.c.firstVisit.isnot(None),
                subquery_firstLab.c.firstLab.isnot(None),
            )
        )
        .subquery()
    )

    # find first antihiv test result
    subquery_firstAntiHIV = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstAntiHIV"),
        )
        .filter(
            and_(
                InvestigationModel.antiHIV.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    subquery_firstAntiHIVResult = (
        db.session.query(
            InvestigationModel.date.label("firstAntiHIV"),
            InvestigationModel.antiHIV.label("firstAntiHIVResult"),
            InvestigationModel.patientID,
        )
        .outerjoin(
            subquery_firstAntiHIV,
            subquery_firstAntiHIV.c.patientID == InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_firstAntiHIV.c.firstAntiHIV == InvestigationModel.date
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
        .filter(
            and_(
                InvestigationModel.antiHIV != "Negative",
                ~InvestigationModel.antiHIV.contains("Incon"),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
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

    # find initial ARV
    subquery_arvInitiationDate = (
        db.session.query(
            VisitModel.patientID,
            func.min(VisitModel.date).label("arvInitiationDate"),
        )
        .filter(
            and_(
                func.array_length(VisitModel.arvMedications, 1) != 0,
                VisitModel.date.between(startDate, endDate),
            )
        )
        .group_by(VisitModel.patientID)
        .subquery()
    )

    subquery_initialARV = (
        db.session.query(
            subquery_arvInitiationDate.c.arvInitiationDate,
            VisitModel.arvMedications.label("initialARV"),
            VisitModel.patientID,
        )
        .outerjoin(
            subquery_arvInitiationDate,
            subquery_arvInitiationDate.c.patientID == VisitModel.patientID,
        )
        .filter(
            and_(
                subquery_arvInitiationDate.c.arvInitiationDate
                == VisitModel.date,
                subquery_arvInitiationDate.c.arvInitiationDate.isnot(None),
            )
        )
        .subquery()
    )

    # find days to start ARV
    subquery_timeToStartARV_raw = (
        db.session.query(
            PatientModel.id.label("patientID"),
            (
                subquery_arvInitiationDate.c.arvInitiationDate
                - subquery_firstPosAntiHIV.c.firstPosAntiHIV
            ).label("timeToStartARV"),
        )
        .outerjoin(
            subquery_arvInitiationDate,
            subquery_arvInitiationDate.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_firstPosAntiHIV,
            subquery_firstPosAntiHIV.c.patientID == PatientModel.id,
        )
        .filter(
            and_(
                subquery_arvInitiationDate.c.arvInitiationDate.isnot(None),
                subquery_firstPosAntiHIV.c.firstPosAntiHIV.isnot(None),
            )
        )
        .subquery()
    )

    subquery_timeToStartARV = db.session.query(
        subquery_timeToStartARV_raw.c.patientID,
        case(
            [(subquery_timeToStartARV_raw.c.timeToStartARV < 0, 0)],
            else_=subquery_timeToStartARV_raw.c.timeToStartARV,
        ).label("timeToStartARV"),
    ).subquery()

    # find last/current ARV regimen
    subquery_lastARVPrescriptionDate = (
        db.session.query(
            VisitModel.patientID,
            func.max(VisitModel.date).label("lastARVPrescriptionDate"),
        )
        .filter(
            and_(
                func.array_length(VisitModel.arvMedications, 1) != 0,
                VisitModel.date.between(startDate, endDate),
            )
        )
        .group_by(VisitModel.patientID)
        .subquery()
    )

    subquery_currentARV = (
        db.session.query(
            subquery_lastARVPrescriptionDate.c.lastARVPrescriptionDate,
            VisitModel.arvMedications.label("currentARV"),
            VisitModel.patientID,
        )
        .outerjoin(
            subquery_lastARVPrescriptionDate,
            subquery_lastARVPrescriptionDate.c.patientID
            == VisitModel.patientID,
        )
        .filter(
            and_(
                subquery_lastARVPrescriptionDate.c.lastARVPrescriptionDate
                == VisitModel.date
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
        .filter(
            and_(
                InvestigationModel.viralLoad.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    subquery_lastVLResults_raw = (
        db.session.query(
            subquery_lastVLLabDate.c.lastViralLoadDate,
            InvestigationModel.viralLoad.label("lastViralLoad"),
            InvestigationModel.patientID,
        )
        .outerjoin(
            subquery_lastVLLabDate,
            subquery_lastVLLabDate.c.patientID == InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_lastVLLabDate.c.lastViralLoadDate
                == InvestigationModel.date
            )
        )
        .subquery()
    )

    subquery_lastVLResults = db.session.query(
        subquery_lastVLResults_raw.c.patientID,
        subquery_lastVLResults_raw.c.lastViralLoadDate,
        case(
            [
                (
                    subquery_lastVLResults_raw.c.lastViralLoad == -1,
                    "Undetectable",
                )
            ],
            else_=cast(subquery_lastVLResults_raw.c.lastViralLoad, Unicode),
        ).label("lastViralLoad"),
    ).subquery()

    # find first CD4
    subquery_firstCD4LabDate = (
        db.session.query(
            InvestigationModel.patientID,
            func.min(InvestigationModel.date).label("firstCD4LabDate"),
        )
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .group_by(InvestigationModel.patientID)
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
        .outerjoin(
            subquery_firstCD4LabDate,
            subquery_firstCD4LabDate.c.patientID
            == InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_firstCD4LabDate.c.firstCD4LabDate
                == InvestigationModel.date
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
        .filter(
            and_(
                InvestigationModel.absoluteCD4.isnot(None),
                InvestigationModel.date.between(startDate, endDate),
            )
        )
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    subquery_lastCD4Results = (
        db.session.query(
            InvestigationModel.date.label("lastCD4LabDate"),
            InvestigationModel.absoluteCD4.label("lastCD4Result"),
            InvestigationModel.percentCD4.label("lastPercentCD4Result"),
            InvestigationModel.patientID,
        )
        .outerjoin(
            subquery_lastCD4LabDate,
            subquery_lastCD4LabDate.c.patientID
            == InvestigationModel.patientID,
        )
        .outerjoin(
            subquery_firstCD4Results,
            subquery_firstCD4Results.c.patientID
            == InvestigationModel.patientID,
        )
        .filter(
            and_(
                subquery_lastCD4LabDate.c.lastCD4LabDate
                == InvestigationModel.date,
                ~(
                    subquery_lastCD4LabDate.c.lastCD4LabDate
                    == subquery_firstCD4Results.c.firstCD4LabDate
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
                VisitModel.date.between(startDate, endDate),
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
        .filter(
            VisitModel.patientID == subquery_unnestDxBeforeARV.c.patientID,
            ~subquery_unnestDxBeforeARV.c.unnestDxBeforeARV.ilike("%B20%"),
        )
        .group_by(VisitModel.patientID)
        .subquery()
    )

    # determine retention
    subquery_lastVisit = (
        db.session.query(
            VisitModel.patientID, func.max(VisitModel.date).label("lastVisit")
        )
        .filter(VisitModel.date.between(startDate, endDate))
        .group_by(VisitModel.patientID)
        .subquery()
    )

    subquery_lastIx = (
        db.session.query(
            InvestigationModel.patientID,
            func.max(InvestigationModel.date).label("lastIx"),
        )
        .filter(InvestigationModel.date.between(startDate, endDate))
        .group_by(InvestigationModel.patientID)
        .subquery()
    )

    subquery_lastClinicVisit = (
        db.session.query(
            PatientModel.id.label("patientID"),
            func.greatest(
                func.coalesce(subquery_lastVisit.c.lastVisit, date.min),
                func.coalesce(subquery_lastIx.c.lastIx, date.min),
            ).label("lastClinicVisit"),
        )
        .outerjoin(
            subquery_lastVisit,
            subquery_lastVisit.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_lastIx, subquery_lastIx.c.patientID == PatientModel.id
        )
        .subquery()
    )

    # construct data_dict
    data_dict = (
        db.session.query(
            cast(PatientModel.id, Unicode).label("System ID"),
            PatientModel.clinicID.label("Clinic ID"),
            PatientModel.hn.label("HN"),
            PatientModel.governmentID.label("ID"),
            PatientModel.napID.label("NAP"),
            PatientModel.name.label("Name"),
            func.to_char(PatientModel.dateOfBirth, "DD-MM-YYYY").label("Date of birth"),
            cast(func.age(PatientModel.dateOfBirth), Unicode).label("Age"),
            PatientModel.sex.label("Sex"),
            PatientModel.gender.label("Gender"),
            PatientModel.maritalStatus.label("Marital status"),
            PatientModel.nationality.label("Nationality"),
            PatientModel.address.label("Address"),
            PatientModel.healthInsurance.label("Healthcare scheme"),
            PatientModel.cares.label("PCU/SMC/Frequent clinic"),
            func.array_to_string(PatientModel.phoneNumbers, joinArrayBy).label("Phone number"),
            func.array_to_string(
                PatientModel.relativePhoneNumbers, joinArrayBy
            ).label("Relative's phone number"),
            PatientModel.referralStatus.label("Referral status"),
            PatientModel.referredFrom.label("Referred from"),
            func.array_to_string(PatientModel.riskBehaviors, joinArrayBy).label("Risk behaviors"),
            PatientModel.patientStatus.label("Patient status"),
            PatientModel.referredOutTo.label("Referred out to"),
            subquery_numberOfPartners.c.numberOfPartners.label("Number of partners"),
            func.to_char(subquery_registerDate.c.registerDate, "DD-MM-YYYY").label("Register date"),
            func.to_char(subquery_lastClinicVisit.c.lastClinicVisit, "DD-MM-YYYY").label("Last visit date"),
            cast(
                (
                    subquery_lastClinicVisit.c.lastClinicVisit
                    - subquery_registerDate.c.registerDate
                )
                / 30,
                Float,
            ).label("Retention period (months)"),
            func.to_char(subquery_firstAntiHIVResult.c.firstAntiHIV, "DD-MM-YYYY").label("First anti-HIV testing date"),
            subquery_firstAntiHIVResult.c.firstAntiHIVResult.label("First anti-HIV testing result"),
            func.to_char(subquery_firstPosAntiHIV.c.firstPosAntiHIV, "DD-MM-YYYY").label("First anti-HIV positive date"),
            func.to_char(subquery_initialARV.c.arvInitiationDate, "DD-MM-YYYY").label("ARV initiation date"),
            func.array_to_string(
                subquery_initialARV.c.initialARV, joinArrayBy
            ).label("First ARV regimen"),
            subquery_timeToStartARV.c.timeToStartARV.label("# of days to start ARV"),
            func.to_char(subquery_currentARV.c.lastARVPrescriptionDate, "DD-MM-YYYY").label("Last ARV prescription date"),
            func.array_to_string(
                subquery_currentARV.c.currentARV, joinArrayBy
            ).label("Last ARV regimen"),
            func.to_char(subquery_lastVLResults.c.lastViralLoadDate, "DD-MM-YYYY").label("Last viral load date"),
            subquery_lastVLResults.c.lastViralLoad.label("Last viral load result"),
            func.to_char(subquery_firstCD4Results.c.firstCD4LabDate, "DD-MM-YYYY").label("First CD4 date"),
            subquery_firstCD4Results.c.firstCD4Result.label("First CD4 result"),
            subquery_firstCD4Results.c.firstPercentCD4Result.label("First %CD4 result"),
            func.to_char(subquery_lastCD4Results.c.lastCD4LabDate, "DD-MM-YYYY").label("Last CD4 date"),
            subquery_lastCD4Results.c.lastCD4Result.label("Last CD4 result"),
            subquery_lastCD4Results.c.lastPercentCD4Result.label("Last %CD4 result"),
            func.array_to_string(
                subquery_DxBeforeARV.c.DxBeforeARV, joinArrayBy
            ).label("Other diagnosis before ARV initiation")
        )
        .outerjoin(
            subquery_numberOfPartners,
            subquery_numberOfPartners.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_registerDate,
            subquery_registerDate.c.patientID == PatientModel.id,
        )
        .outerjoin(
            subquery_lastClinicVisit,
            subquery_lastClinicVisit.c.patientID == PatientModel.id,
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
            subquery_timeToStartARV,
            subquery_timeToStartARV.c.patientID == PatientModel.id,
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
                subquery_registerDate.c.registerDate.between(
                    startDate, endDate
                ),
            )
        )
        .order_by(PatientModel.clinicID)
        .order_by(PatientModel.dateOfBirth)
        .order_by(subquery_firstPosAntiHIV.c.firstPosAntiHIV)
        .statement
    )

    df = pd.read_sql(data_dict, db.session.bind)

    # replace missing values to None
    df = df.where(df.notnull(), None)

    return df
