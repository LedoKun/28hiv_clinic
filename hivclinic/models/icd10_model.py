import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID

from hivclinic import db


class ICD10Model(db.Model):
    __tablename__ = "icd10"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sqlalchemy.text("uuid_generate_v4()"),
    )

    icd10 = db.Column(db.Unicode(), nullable=False)
    description = db.Column(db.Unicode(), nullable=False)
