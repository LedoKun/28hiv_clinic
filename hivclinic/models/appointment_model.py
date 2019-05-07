from hivclinic import db
from hivclinic.models import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class AppointmentModel(BaseModel):
    __tablename__ = "appointment"
    relationship_keys = {"patientID"}

    date = db.Column(db.Date(), nullable=False)
    appointmentFor = db.Column(db.Unicode(), nullable=False)

    # parent id
    patientID = db.Column(UUID(as_uuid=True), db.ForeignKey("patient.id"))
