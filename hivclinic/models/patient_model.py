from sqlalchemy.dialects.postgresql import ARRAY

from hivclinic import db
from hivclinic.models import BaseModel
from hivclinic.models.appointment_model import AppointmentModel
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.visit_model import VisitModel


class PatientModel(BaseModel):
    __tablename__ = "patient"
    relationship_keys = [
        "partners",
        "visits",
        "investigations",
        "appointments",
    ]

    clinicID = db.Column(db.Unicode(), unique=True, nullable=True)
    hn = db.Column(db.Unicode(), nullable=False, unique=True)
    governmentID = db.Column(db.Unicode())
    napID = db.Column(db.Unicode())

    name = db.Column(db.Unicode(), nullable=False)
    dateOfBirth = db.Column(db.Date())

    sex = db.Column(db.Unicode(), nullable=False)
    gender = db.Column(db.Unicode())
    maritalStatus = db.Column(db.Unicode())
    nationality = db.Column(db.Unicode())

    occupation = db.Column(db.Unicode())
    education = db.Column(db.Unicode())

    healthInsurance = db.Column(db.Unicode(), nullable=False)

    phoneNumbers = db.Column(ARRAY(db.Unicode()))
    relativePhoneNumbers = db.Column(ARRAY(db.Unicode()))

    referralStatus = db.Column(db.Unicode())
    referredFrom = db.Column(db.Unicode())

    patientStatus = db.Column(db.Unicode())
    referredOutTo = db.Column(db.Unicode())

    riskBehaviors = db.Column(ARRAY(db.Unicode()))

    # relationship
    partners = db.relationship(
        PartnerModel,
        backref="patient",
        order_by="desc(PartnerModel.created_on)",
        cascade="all, delete, delete-orphan",
        collection_class=set,
        lazy="dynamic",
    )
    visits = db.relationship(
        VisitModel,
        backref="patient",
        order_by="desc(VisitModel.date)",
        cascade="all, delete, delete-orphan",
        collection_class=set,
        lazy="dynamic",
    )
    investigations = db.relationship(
        InvestigationModel,
        backref="patient",
        order_by="desc(InvestigationModel.date)",
        cascade="all, delete, delete-orphan",
        collection_class=set,
        lazy="dynamic",
    )
    appointments = db.relationship(
        AppointmentModel,
        backref="patient",
        order_by="desc(AppointmentModel.date)",
        cascade="all, delete, delete-orphan",
        collection_class=set,
        lazy="dynamic",
    )
