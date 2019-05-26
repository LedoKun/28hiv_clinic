from . import BaseSchema
from hivclinic.models.appointment_model import AppointmentModel
from marshmallow import fields


class AppointmentSchema(BaseSchema):
    date = fields.Date(required=True)
    appointmentFor = fields.Str(required=True)

    # parent id
    patientID = fields.Nested(
        "PatientSchema",
        exclude=["partners", "visits", "investigations", "appointments"],
    )

    class Meta:
        model = AppointmentModel
        transient = True
