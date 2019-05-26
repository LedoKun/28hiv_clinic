from flask_restplus import Resource
from marshmallow import validate
from webargs import fields
from webargs.flaskparser import use_args

from hivclinic import db
from hivclinic.models.patient_model import PatientModel

from . import api

is_unique = {
    "field_name": fields.Str(
        required=True,
        validate=validate.OneOf(["hn", "clinicID", "governmentID", "napID"]),
    ),
    "keyword": fields.Str(required=True),
}


@api.route("/is_unique")
class IsFieldUnique(Resource):
    @api.doc("check_if_the_field_is_unique")
    @use_args(is_unique, locations=("querystring",))
    def get(self, args):
        """Check if the field is unique"""
        exists = (
            db.session.query(PatientModel.id)
            .filter(
                getattr(PatientModel, args["field_name"]) == args["keyword"]
            )
            .scalar()
            is None
        )

        return exists, 200
