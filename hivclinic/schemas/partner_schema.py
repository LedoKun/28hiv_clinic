from hivclinic.models.partner_model import PartnerModel
from marshmallow import fields

from . import BaseSchema


class PartnerSchema(BaseSchema):
    deceased = fields.Str(required=True)

    sex = fields.Str(required=True)
    gender = fields.Str(required=True)
    HIVStatus = fields.Str(required=True)
    # PatientHIVStatusDisclosure = fields.Str()
    # HIVTreatmentOrPrevention = fields.Str()

    # clinicAttend = fields.Str()
    # hn = fields.Str()

    # parent id
    patientID = fields.Nested(
        "PatientSchema",
        exclude=["partners", "visits", "investigations", "appointments"],
    )

    class Meta:
        model = PartnerModel
        transient = True
