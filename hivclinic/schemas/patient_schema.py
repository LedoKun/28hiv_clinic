from . import BaseSchema
from hivclinic.models.patient_model import PatientModel
from hivclinic.schemas.partner_schema import PartnerSchema
from hivclinic.schemas.visit_schema import VisitSchema
from hivclinic.schemas.investigation_schema import InvestigationSchema
from hivclinic.schemas.appointment_schema import AppointmentSchema
from marshmallow import fields, validates_schema, ValidationError


class PatientSchema(BaseSchema):
    # clinicID = fields.String()
    hn = fields.String(required=True)
    # governmentID = fields.String()
    # napID = fields.String()

    name = fields.String(required=True)
    # dateOfBirth = fields.Date()

    sex = fields.String(required=True)
    # gender = fields.String()
    # maritalStatus = fields.String()
    # nationality = fields.String()
    # educationLevel = fields.String()
    healthInsurance = fields.String(required=True)

    # address = fields.String()

    # phoneNumbers = fields.List(fields.String())
    # relativePhoneNumbers = fields.List(fields.String())

    # referralStatus = fields.String()
    # referredFrom = fields.String()

    # riskBehaviors = fields.List(fields.String())

    # patientStatus = fields.String()

    # relationship
    partners = fields.Nested(PartnerSchema, many=True, exclude=["patient"])
    visits = fields.Nested(VisitSchema, many=True, exclude=["patient"])
    investigations = fields.Nested(
        InvestigationSchema, many=True, exclude=["patient"]
    )
    appointments = fields.Nested(
        AppointmentSchema, many=True, exclude=["patient"]
    )

    @validates_schema
    def validate_unique_ids(self, data):
        unique_fields = ["hn", "clinicID", "napID"]

        for fieldname in unique_fields:
            if fieldname not in data.keys():
                continue

            existed_patient = PatientModel.query.filter(
                getattr(PatientModel, fieldname) == data[fieldname]
            ).first()

            if not existed_patient:
                continue

            if existed_patient and "id" not in data.keys():
                raise ValidationError({fieldname: f"The data must be unique."})

            if existed_patient.id != data["id"]:
                raise ValidationError({fieldname: f"The data must be unique."})

    class Meta:
        model = PatientModel
