from flask import abort, jsonify
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from api.models import icd10Model
from api.schemas import icd10Schema

search_args = {"keyword": fields.Str(required=True)}


class icd10Search(Resource):
    @use_args(search_args)
    def get(self, args):
        if args["keyword"] is None:
            abort(422)

        results = (
            icd10Model.query.filter(
                icd10Model.icd10WithDescription.ilike(
                    "%{}%".format(args["keyword"])
                )
            )
            .limit(10)
            .all()
        )

        icd10_schema = icd10Schema(only=["icd10WithDescription"], many=True)

        results = icd10_schema.dump(results).data
        results_list = [item["icd10WithDescription"] for item in results]

        return jsonify(results_list)
