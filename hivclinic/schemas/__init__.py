from hivclinic import ma, db

# from marshmallow import fields


class BaseSchema(ma.ModelSchema):
    # id = fields.UUID()
    # created_on = fields.Date()
    # modified_on = fields.Date()

    class Meta:
        strict = True
        sqla_session = db.session
        datetimeformat = "iso"
