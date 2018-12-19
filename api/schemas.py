from marshmallow import Schema, fields, validate
from api import db


Schema.TYPE_MAPPING[db.Column(db.Integer())] = fields.Integer
Schema.TYPE_MAPPING[db.Column(db.Unicode())] = fields.String


class BaseSchema(Schema):
    def __repr__(self):
        return "<BaseSchema(name={self.__class__.__name__!r})>".format(
            self=self
        )

    def __str__(self):
        return str(self.__repr__)

    class Meta:
        strict = True
        additional = ["id"]


class ICD10Schema(BaseSchema):
    icd10WithDescription = fields.String(required=True)


class UserSchema(BaseSchema):
    username = fields.String(validate=lambda p: len(p) >= 5, required=True)
    password = fields.String(validate=lambda p: len(p) >= 5, required=True)


class VisitSchema(BaseSchema):
    date = fields.Date(required=True)
    bw = fields.Float(validate=lambda p: 0.0 <= p, missing=None)
    contactTB = fields.String(
        validate=validate.OneOf(
            ["Contacted with TB", "Not Contacted with TB"]
        ),
        missing=None,
    )
    adherenceScale = fields.Integer(
        validate=lambda p: 0 <= p <= 100, missing=None
    )
    adherenceProblem = fields.String(
        validate=lambda p: len(p) >= 2, missing=None
    )
    delayedDosing = fields.Integer(validate=lambda p: 0 <= p, missing=None)
    impression = fields.List(fields.String(required=True), required=True)
    arv = fields.List(
        fields.String(validate=lambda p: len(p) >= 2, missing=None),
        missing=None,
    )
    oiProphylaxis = fields.List(
        fields.String(validate=lambda p: len(p) >= 2, missing=None),
        missing=None,
    )
    antiTB = fields.List(
        fields.String(validate=lambda p: len(p) >= 2, missing=None),
        missing=None,
    )
    vaccination = fields.List(
        fields.String(validate=lambda p: len(p) >= 2, missing=None),
        missing=None,
    )

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class InvestigationSchema(BaseSchema):
    date = fields.Date(required=True)
    antiHIV = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    cd4 = fields.Integer(validate=lambda p: 0 <= p, missing=None)
    pCD4 = fields.Float(validate=lambda p: 0 <= p <= 100, missing=None)
    vl = fields.Integer(validate=lambda p: 0 <= p, missing=None)
    vdrl = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    rpr = fields.Integer(validate=lambda p: 0 <= p, missing=None)
    hbsag = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    antiHBs = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    antiHCV = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    ppd = fields.Integer(validate=lambda p: 0 <= p, missing=None)
    cxr = fields.String(validate=lambda p: len(p) >= 2, missing=None)
    tb = fields.String(
        validate=validate.OneOf(
            [
                "AFB +",
                "Culture + for MTB",
                "GeneXpert + for MTB",
                "GeneXpert + for Rifampicin Resistance MTB",
                "Negative",
            ]
        ),
        missing=None,
    )
    hivResistence = fields.String(
        validate=lambda p: len(p) >= 2, missing=None
    )

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class AppointmentSchema(BaseSchema):
    date = fields.Date(required=True)
    appointmentFor = fields.String(
        validate=lambda p: len(p) >= 2, required=True
    )

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class PatientSchema(BaseSchema):
    hn = fields.String(validate=lambda p: len(p) >= 2, required=True)
    gid = fields.String(validate=lambda p: len(p) >= 2, missing=None)
    cid = fields.String(validate=lambda p: len(p) >= 2, missing=None)
    nap = fields.String(validate=lambda p: len(p) >= 2, missing=None)
    name = fields.String(validate=lambda p: len(p) >= 2, required=True)
    dob = fields.Date(allow_none=True, required=True)
    sex = fields.String(
        validate=validate.OneOf(["ชาย", "หญิง", "-"]), required=True
    )
    gender = fields.String(
        validate=validate.OneOf(
            ["Heterosexual", "Homosexual", "Lesbian", "Bisexual", "-"]
        ),
        allow_none=True,
    )
    marital = fields.String(
        validate=validate.OneOf(["โสด", "สมรส", "ม่าย", "-"]), missing=None
    )
    nationality = fields.String(allow_none=True)
    payer = fields.String(
        validate=validate.OneOf(
            [
                "ประกันสุขภาพทั่วหน้า",
                "ประกันสุขภาพทั่วหน้า นอกเขต",
                "ประกันสังคม",
                "ประกันสังคมต่าง รพ.",
                "ข้าราชการ/จ่ายตรง",
                "ต่างด้าว",
                "ชำระเงิน",
            ]
        ),
        required=True,
    )
    isRefer = fields.String(
        validate=validate.OneOf(
            [
                "ผู้ป่วยใหม่",
                "ผู้ป่วยรับโอน (ยังไม่เริ่ม ARV)",
                "ผู้ป่วยรับโอน (เริ่ม ARV แล้ว)",
            ]
        ),
        required=True,
    )
    referFrom = fields.String(validate=lambda p: len(p) >= 2, missing=None)
    education = fields.String(
        validate=validate.OneOf(
            [
                "ต่ำกว่ามัธยมศึกษาตอนปลาย",
                "มัธยมศึกษาตอนปลาย",
                "ปวช/ปวส",
                "ปริญญาตรี",
                "ปริญญาโท",
                "ปริญญาเอก",
                "-",
            ]
        ),
        allow_none=True,
    )
    tel = fields.List(
        fields.String(allow_none=True, validate=lambda p: len(p) >= 1),
        allow_none=True,
    )
    relative_tel = fields.List(
        fields.String(allow_none=True, validate=lambda p: len(p) >= 1),
        allow_none=True,
    )
    address = fields.String(validate=lambda p: len(p) >= 2, missing=None)

    # relationship
    visits = fields.Nested(VisitSchema, many=True)
    investigation = fields.Nested(InvestigationSchema, many=True)
    appointments = fields.Nested(AppointmentSchema, many=True)
