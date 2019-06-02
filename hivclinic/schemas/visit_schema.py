from . import BaseSchema
from hivclinic.models.visit_model import VisitModel
from marshmallow import fields


class VisitSchema(BaseSchema):
    date = fields.Date(required=True)

    # bodyWeight = fields.Float()

    # historyOfContactWithTB = fields.Boolean()

    # ARTAdherenceScale = fields.Float()
    # ARTAvgDelayedDosing = fields.Float()
    # ARTAdherenceProblem = fields.Str()

    # impression = fields.List(fields.Str())
    # impression = fields.List(fields.Str(required=True), required=True)

    # arv = fields.List(fields.Str())
    # whySwitchingARV = fields.Str()
    # otherMedication = fields.List(fields.Str())

    # parent id
    patientID = fields.Nested(
        "PatientSchema",
        exclude=["partners", "visits", "investigations", "appointments"],
    )

    class Meta:
        model = VisitModel
        transient = True
