from . import BaseSchema
from hivclinic.models.investigation_model import InvestigationModel
from marshmallow import fields, validates_schema, ValidationError


class InvestigationSchema(BaseSchema):
    date = fields.Date(required=True)

    # # hiv related tests
    # viralLoad = fields.Str()
    # percentCD4 = fields.Float()
    # absoluteCD4 = fields.Float()

    # # cbc
    # hemoglobin = fields.Float()
    # hematocrit = fields.Float()
    # whiteBloodCellCount = fields.Float()

    # neutrophilPct = fields.Float()
    # eosinophilPct = fields.Float()
    # basophilPct = fields.Float()
    # lymphocytePct = fields.Float()
    # monophilPct = fields.Float()

    # # metabolic
    # fbs = fields.Float()
    # hemoglobinA1c = fields.Float()

    # cholesterol = fields.Float()
    # triglycerides = fields.Float()

    # creatinine = fields.Float()

    # ast = fields.Float()
    # alt = fields.Float()
    # alp = fields.Float()

    # sodium = fields.Float()
    # potassium = fields.Float()
    # chloride = fields.Float()
    # bicarbonate = fields.Float()
    # phosphate = fields.Float()

    # # serology
    # antiHIV = fields.Str()
    # HBsAg = fields.Str()
    # antiHBs = fields.Str()
    # antiHCV = fields.Str()
    # vdrl = fields.Str()
    # rpr = fields.Integer()
    # cryptoAg = fields.Str()

    # # tb
    # afb = fields.Str()
    # geneXpert = fields.Str()
    # sputumCulture = fields.Str()
    # dst = fields.Str()
    # tst = fields.Float()

    # # cxr
    # chestXRay = fields.Str()

    # parent id
    patientID = fields.Nested(
        "PatientSchema",
        exclude=["partners", "visits", "investigations", "appointments"],
    )

    @validates_schema
    def validate_rpr(self, data):
        if (
            "rpr" in data.keys()
            and data["rpr"]
            and (int(data["rpr"]) % 2 != 0 or int(data["rpr"]) == 1)
        ):
            raise ValidationError(
                {"rpr": "RPR titer must be one or divisable by two."}
            )

    @validates_schema
    def validate_lab_input(self, data):
        count_not_null = 0

        if not (len(data) >= 2):
            raise ValidationError("Enter at least one investigation result.")

        for key in data:
            skip_keys = (
                set(InvestigationModel.do_not_update_keys)
                | set(InvestigationModel.relationship_keys)
                | set(InvestigationModel.protected_keys)
                | set(["modified_on"])
            )

            if key in skip_keys:
                continue

            if not data[key]:
                count_not_null = count_not_null + 1

        if not count_not_null >= 2:
            raise ValidationError("Enter at least one investigation result.")

    class Meta:
        model = InvestigationModel
        transient = True
