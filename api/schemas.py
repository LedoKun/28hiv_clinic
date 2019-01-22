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
    username = fields.String(validate=validate.Length(min=5), required=True)
    password = fields.String(validate=validate.Length(min=5), required=True)


class VisitSchema(BaseSchema):
    id = fields.String(missing=None)
    date = fields.Date(required=True)

    bw = fields.Float(validate=validate.Range(min=0), missing=None)
    contactTB = fields.String(missing=None)
    adherenceScale = fields.Integer(
        validate=validate.Range(min=0, max=100), missing=None
    )
    adherenceProblem = fields.String(missing=None)
    delayedDosing = fields.Integer(
        validate=validate.Range(min=0), missing=None
    )
    impression = fields.List(
        fields.String(required=True),
        validate=validate.Length(min=1),
        required=True,
    )
    arv = fields.List(fields.String(missing=None), missing=None)
    whySwitch = fields.String(missing=None)
    oiProphylaxis = fields.List(fields.String(missing=None), missing=None)
    antiTB = fields.List(fields.String(missing=None), missing=None)
    vaccination = fields.List(fields.String(missing=None), missing=None)

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class InvestigationSchema(BaseSchema):
    id = fields.String(missing=None)
    date = fields.Date(required=True)

    # hiv labs
    antiHIV = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    cd4 = fields.Integer(validate=validate.Range(min=0), missing=None)
    pCD4 = fields.Float(validate=validate.Range(min=0, max=100), missing=None)
    vl = fields.Integer(validate=validate.Range(min=0), missing=None)

    # sy labs
    tpha = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    vdrl = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    rpr = fields.Integer(validate=validate.Range(min=0), missing=None)

    # cbc
    wbc = fields.Float(validate=validate.Range(min=0), missing=None)
    hb = fields.Float(validate=validate.Range(min=0), missing=None)
    hct = fields.Float(validate=validate.Range(min=0, max=100), missing=None)
    wbcPNeu = fields.Float(
        validate=validate.Range(min=0, max=100), missing=None
    )
    wbcPLym = fields.Float(
        validate=validate.Range(min=0, max=100), missing=None
    )
    wbcPEos = fields.Float(
        validate=validate.Range(min=0, max=100), missing=None
    )
    wbcPBasos = fields.Float(
        validate=validate.Range(min=0, max=100), missing=None
    )
    wbcPMono = fields.Float(
        validate=validate.Range(min=0, max=100), missing=None
    )

    # bun cr e'lyte
    bun = fields.Float(validate=validate.Range(min=0), missing=None)
    cr = fields.Float(validate=validate.Range(min=0), missing=None)

    na = fields.Float(validate=validate.Range(min=0), missing=None)
    k = fields.Float(validate=validate.Range(min=0), missing=None)
    cl = fields.Float(validate=validate.Range(min=0), missing=None)
    hco3 = fields.Float(validate=validate.Range(min=0), missing=None)
    ca = fields.Float(validate=validate.Range(min=0), missing=None)
    mg = fields.Float(validate=validate.Range(min=0), missing=None)
    po4 = fields.Float(validate=validate.Range(min=0), missing=None)

    # fbs
    fbs = fields.Integer(validate=validate.Range(min=0), missing=None)
    hba1c = fields.Float(validate=validate.Range(min=0), missing=None)

    # ua
    urine_glucose_dipstick = fields.Float(
        validate=validate.Range(min=0), missing=None
    )
    urine_prot_dipstick = fields.Float(
        validate=validate.Range(min=0), missing=None
    )
    urine_glucose = fields.Float(validate=validate.Range(min=0), missing=None)
    urine_prot_cr_ratio = fields.Float(
        validate=validate.Range(min=0), missing=None
    )

    # lipid profile
    chol = fields.Integer(validate=validate.Range(min=0), missing=None)
    tg = fields.Integer(validate=validate.Range(min=0), missing=None)
    hdl = fields.Integer(validate=validate.Range(min=0), missing=None)
    ldl = fields.Integer(validate=validate.Range(min=0), missing=None)

    # lft
    total_prot = fields.Float(validate=validate.Range(min=0), missing=None)
    albumin = fields.Float(validate=validate.Range(min=0), missing=None)
    globulin = fields.Float(validate=validate.Range(min=0), missing=None)
    total_bilirubin = fields.Float(
        validate=validate.Range(min=0), missing=None
    )
    direct_bilirubin = fields.Float(
        validate=validate.Range(min=0), missing=None
    )
    alt = fields.Float(validate=validate.Range(min=0), missing=None)
    ast = fields.Float(validate=validate.Range(min=0), missing=None)
    alp = fields.Float(validate=validate.Range(min=0), missing=None)

    # hepatitis serology
    hbsag = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    antiHBs = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    antiHCV = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )

    # other serology
    cryptoAgBlood = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )
    cryptoAgCSF = fields.String(
        validate=validate.OneOf(["+ ve", "- ve", "?"]), missing=None
    )

    # hiv mutations
    hivResistance = fields.List(
        fields.String(required=True),
        validate=validate.Length(min=0),
        missing=None,
    )
    hivMutation = fields.List(
        fields.String(required=True),
        validate=validate.Length(min=0),
        missing=None,
    )

    # tb labs
    ppd = fields.Integer(validate=validate.Range(min=0), missing=None)
    cxr = fields.String(missing=None)

    afb = fields.String(missing=None)
    sputumCulture = fields.String(missing=None)
    dst = fields.List(
        fields.String(required=True),
        validate=validate.Length(min=0),
        missing=None,
    )
    geneXpert = fields.String(missing=None)
    lineProbeAssay = fields.String(missing=None)

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class AppointmentSchema(BaseSchema):
    id = fields.String(missing=None)
    date = fields.Date(required=True)
    appointmentFor = fields.String(required=True)

    # relationship
    patient = fields.Nested(
        "PatientSchema", exclude=("visits", "investigation", "appointments")
    )


class PatientSchema(BaseSchema):
    hn = fields.String(required=True)
    gid = fields.String(missing=None)
    cid = fields.String(missing=None)
    nap = fields.String(missing=None)
    patientStatus = fields.String(
        validate=validate.OneOf(
            [
                "รักษาต่อเนื่อง",
                "ส่งตัว/รับการรักษาที่สภานพยาบาลอื่น ในประเทศไทย",
                "ส่งตัว/รับการรักษาที่สภานพยาบาลอื่น ในต่างประเทศ",
                "ถูกส่งกลับประเทศ",
                "ขาดการติดต่อ",
                "เสียชีวิต",
            ]
        ),
        missing="รักษาต่อเนื่อง",
        default="รักษาต่อเนื่อง"
    )
    referOutTo = fields.String(missing=None)
    name = fields.String(required=True)
    dob = fields.Date(required=True)
    sex = fields.String(
        validate=validate.OneOf(["ชาย", "หญิง", "-"]), required=True
    )
    gender = fields.String(
        validate=validate.OneOf(
            ["Heterosexual", "Homosexual", "Bisexual", "-"]
        ),
        missing=None,
    )
    marital = fields.String(
        validate=validate.OneOf(["โสด", "สมรส", "ม่าย", "หย่า", "-"]),
        missing=None,
    )
    nationality = fields.String(missing=None)
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
    referFrom = fields.String(missing=None)
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
        missing=None,
    )
    tel = fields.List(fields.String(missing=None), missing=None)
    relative_tel = fields.List(fields.String(missing=None), missing=None)
    address = fields.String(missing=None)

    # relationship
    visits = fields.Nested(VisitSchema, many=True)
    investigation = fields.Nested(InvestigationSchema, many=True)
    appointments = fields.Nested(AppointmentSchema, many=True)
