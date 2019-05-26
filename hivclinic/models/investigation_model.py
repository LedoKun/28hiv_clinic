from hivclinic import db
from hivclinic.models import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class InvestigationModel(BaseModel):
    __tablename__ = "investigation"
    relationship_keys = {"patientID"}

    date = db.Column(db.Date(), nullable=False)

    # hiv related tests
    viralLoad = db.Column(db.Float())
    absoluteCD4 = db.Column(db.Float())
    percentCD4 = db.Column(db.Float())

    # cbc
    hemoglobin = db.Column(db.Float())
    hematocrit = db.Column(db.Float())
    whiteBloodCellCount = db.Column(db.Float())

    neutrophilsPct = db.Column(db.Float())
    eosinophilsPct = db.Column(db.Float())
    basophilsPct = db.Column(db.Float())
    lymphocytesPct = db.Column(db.Float())
    monocytesPct = db.Column(db.Float())

    # metabolic
    fbs = db.Column(db.Float())
    hemoglobinA1c = db.Column(db.Float())

    cholesterol = db.Column(db.Float())
    triglycerides = db.Column(db.Float())

    creatinine = db.Column(db.Float())
    eGFR = db.Column(db.Float())

    ast = db.Column(db.Float())
    alt = db.Column(db.Float())
    alp = db.Column(db.Float())

    sodium = db.Column(db.Float())
    potassium = db.Column(db.Float())
    chloride = db.Column(db.Float())
    bicarbonate = db.Column(db.Float())
    phosphate = db.Column(db.Float())

    # serology
    antiHIV = db.Column(db.Unicode())
    HBsAg = db.Column(db.Unicode())
    antiHBs = db.Column(db.Unicode())
    antiHCV = db.Column(db.Unicode())
    tpha = db.Column(db.Unicode())
    rpr = db.Column(db.Integer())
    cryptoAg = db.Column(db.Unicode())

    # tb
    afb = db.Column(db.Unicode())
    geneXpert = db.Column(db.Unicode())
    tbCulture = db.Column(db.Unicode())
    dst = db.Column(db.Unicode())
    lpa = db.Column(db.Unicode())
    tst = db.Column(db.Float())

    # cxr
    chestXRay = db.Column(db.Unicode())

    # parent id
    patientID = db.Column(UUID(as_uuid=True), db.ForeignKey("patient.id"))
