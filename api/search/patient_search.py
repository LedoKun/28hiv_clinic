from flask import abort, jsonify, request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import parser

from api.models import PatientModel
from api.schemas import PatientSchema

search_args = {"keyword": fields.Str(required=True)}


class patientSearch(Resource):
    @jwt_required
    def get(self):
        args = parser.parse(search_args, request)

        if args["keyword"] is None:
            abort(422)

        else:
            args["keyword"] = str(args["keyword"]).replace("_", "/")

        results = (
            PatientModel.query.filter(
                PatientModel.hn.ilike("%{}%".format(args["keyword"]))
                | PatientModel.gid.ilike("%{}%".format(args["keyword"]))
                | PatientModel.cid.ilike("%{}%".format(args["keyword"]))
                | PatientModel.nap.ilike("%{}%".format(args["keyword"]))
                | PatientModel.name.ilike("%{}%".format(args["keyword"]))
            )
            .limit(5)
            .all()
        )

        patient_schema = PatientSchema(
            only=("hn", "name", "nationality"), many=True
        )

        results = patient_schema.dump(results).data

        return jsonify(results)
