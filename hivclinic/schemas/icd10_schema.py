from . import BaseSchema
from hivclinic.models.icd10_model import ICD10Model
from marshmallow import fields


class ICD10Schema(BaseSchema):
    icd10 = fields.Str(required=True)

    class Meta:
        model = ICD10Model
