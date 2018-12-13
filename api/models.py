from datetime import datetime
from passlib.hash import bcrypt
from api import db
from flask import current_app


class BaseModel(db.Model):
    __abstract__ = True

    def __repr__(self):
        return "<BaseModel(name={self.__class__.__name__!r})>".format(self=self)

    def __str__(self):
        return str(self.__repr__)

    def update(self, **kwargs):
        """
        Update column using the provided dictionary
        """
        __skip__ = ["_sa_instance_state"]
        all_keys = list(vars(self).keys())

        for key in all_keys:
            if (
                (key in __skip__)
                or (key in self.__relationship__)
                or (key in self.__protected__)
            ):
                continue

            else:
                setattr(self, key, kwargs[key])

        self.modify_timestamp = datetime.utcnow()

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    modify_timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class PatientModel(BaseModel):
    """
    Store patient information
    """

    __tablename__ = "patient"
    __protected__ = ["id", "hn", "timestamp", "modify_timestamp"]
    __relationship__ = ["visits", "investigations", "appointments"]

    hn = db.Column(db.Unicode(), unique=True)
    gid = db.Column(db.Unicode())
    cid = db.Column(db.Unicode())
    nap = db.Column(db.Unicode())
    name = db.Column(db.Unicode())
    dob = db.Column(db.Date())
    sex = db.Column(db.Unicode())
    gender = db.Column(db.Unicode())
    marital = db.Column(db.Unicode())
    nationality = db.Column(db.Unicode())
    payer = db.Column(db.Unicode())
    isRefer = db.Column(db.Unicode())
    referFrom = db.Column(db.Unicode())
    education = db.Column(db.Unicode())
    tel = db.Column(db.ARRAY(db.Unicode()))
    relative_tel = db.Column(db.ARRAY(db.Unicode()))
    address = db.Column(db.Unicode())

    # relationship
    visits = db.relationship(
        "VisitModel",
        backref="patient",
        lazy="dynamic",
        order_by="desc(VisitModel.date)",
        cascade="all, delete, delete-orphan",
    )
    investigation = db.relationship(
        "InvestigationModel",
        backref="patient",
        lazy="dynamic",
        order_by="desc(InvestigationModel.date)",
        cascade="all, delete, delete-orphan",
    )
    appointments = db.relationship(
        "AppointmentModel",
        backref="patient",
        lazy="dynamic",
        order_by="desc(AppointmentModel.date)",
        cascade="all, delete, delete-orphan",
    )


class VisitModel(BaseModel):
    """
    Store Visit information
    """

    __tablename__ = "visit"
    __protected__ = ["id", "parent_id"]
    __relationship__ = ["patient_id"]

    date = db.Column(db.Date())
    bw = db.Column(db.Float())
    contactTB = db.Column(db.Unicode())
    adherenceScale = db.Column(db.Integer())
    adherenceProblem = db.Column(db.Unicode())
    delayedDosing = db.Column(db.Integer())
    impression = db.Column(db.ARRAY(db.Unicode()))
    arv = db.Column(db.ARRAY(db.Unicode()))
    oiProphylaxis = db.Column(db.ARRAY(db.Unicode()))
    antiTB = db.Column(db.ARRAY(db.Unicode()))
    vaccination = db.Column(db.ARRAY(db.Unicode()))

    # relationship to parent
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class InvestigationModel(BaseModel):
    """
    Store Investigation information
    """

    __tablename__ = "investigation"
    __protected__ = ["id", "parent_id"]
    __relationship__ = ["patient_id"]

    date = db.Column(db.Date())
    antiHIV = db.Column(db.Unicode())
    cd4 = db.Column(db.Integer())
    pCD4 = db.Column(db.Integer())
    vl = db.Column(db.Integer())
    vdrl = db.Column(db.Unicode())
    rpr = db.Column(db.Integer())
    hbsag = db.Column(db.Unicode())
    antiHBs = db.Column(db.Unicode())
    antiHCV = db.Column(db.Unicode())
    ppd = db.Column(db.Integer())
    cxr = db.Column(db.Unicode())
    tb = db.Column(db.Unicode())
    hivResistence = db.Column(db.Unicode())

    # relationship to parent
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class AppointmentModel(BaseModel):
    """
    Store Appointment information
    """

    __tablename__ = "appointment"
    __protected__ = ["id", "parent_id"]
    __relationship__ = ["patient_id"]

    date = db.Column(db.Date())
    appointmentFor = db.Column(db.Unicode())

    # relationship to parent
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class ICD10Model(db.Model):
    """
    Store ICD10 information
    """

    __tablename__ = "icd10"

    id = db.Column(db.Integer, primary_key=True)
    icd10WithDescription = db.Column(db.Unicode)


class UserModel(db.Model):
    """
    Store User information
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(), unique=True, nullable=False)
    password = db.Column(db.Unicode(), nullable=False)

    @staticmethod
    def verify_hash(password, hash):
        return bcrypt.verify(password, hash)

    @staticmethod
    def generate_hash(password):
        return bcrypt.using(rounds=current_app.config["BCRYPT_ROUNDS"]).hash(password)


class RevokedTokenModel(db.Model):
    __tablename__ = "revoked_tokens"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.Unicode(120))

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter(RevokedTokenModel.jti == jti).first()
        return bool(query)
