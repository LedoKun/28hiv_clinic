from hivclinic import db
from hivclinic.models import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY, UUID


class VisitModel(BaseModel):
    __tablename__ = "visit"
    relationship_keys = {"patientID"}
    # protected_keys = {"medications"}

    date = db.Column(db.Date(), nullable=False)

    bodyWeight = db.Column(db.Float())

    historyOfContactWithTB = db.Column(db.Boolean())

    ARTAdherenceScale = db.Column(db.Float())
    ARTAvgDelayedDosing = db.Column(db.Float())
    ARTAdherenceProblem = db.Column(db.Unicode())

    impression = db.Column(ARRAY(db.Unicode()))

    arvMedications = db.Column(ARRAY(db.Unicode()))
    whySwitchingARV = db.Column(db.Unicode())

    tbMedications = db.Column(ARRAY(db.Unicode()))
    oiMedications = db.Column(ARRAY(db.Unicode()))

    medications = db.Column(ARRAY(db.Unicode()))

    # parent id
    patientID = db.Column(UUID(as_uuid=True), db.ForeignKey("patient.id"))
