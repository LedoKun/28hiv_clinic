from hivclinic.models.partner_model import PartnerModel
from marshmallow import fields

from . import BaseSchema


class PartnerSchema(BaseSchema):
    # deceased = fields.Str()

    # gender = fields.Str()
    # HIVStatus = fields.Str()
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
