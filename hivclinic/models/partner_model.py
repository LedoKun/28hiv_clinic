from sqlalchemy.dialects.postgresql import ARRAY

from hivclinic import db
from hivclinic.models import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class PartnerModel(BaseModel):
    __tablename__ = "partner"
    relationship_keys = {"patientID"}

    deceased = db.Column(db.Unicode())

    sex = db.Column(db.Unicode())
    gender = db.Column(db.Unicode())
    HIVStatus = db.Column(db.Unicode())
    PatientHIVStatusDisclosure = db.Column(db.Unicode())
    HIVTreatmentOrPrevention = db.Column(ARRAY(db.Unicode()))

    clinicAttend = db.Column(db.Unicode())
    hn = db.Column(db.Unicode())

    # parent id
    patientID = db.Column(UUID(as_uuid=True), db.ForeignKey("patient.id"))
