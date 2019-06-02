from flask_restplus import Resource
from webargs import fields
from webargs.flaskparser import use_args

from hivclinic.models.icd10_model import ICD10Model
from hivclinic.schemas.icd10_schema import ICD10Schema

from . import api


@api.route("/icd10/search")
class ICD10Resource(Resource):
    @api.doc("search_icd10_entries")
    @use_args(
        {"keyword": fields.Str(required=True)}, locations=("querystring",)
    )
    def get(self, args):
        """Check if the field is unique"""
        icd10_schema = ICD10Schema(many=True)

        icd10s_query = (
            ICD10Model.query.order_by(ICD10Model.id)
            .filter(
                ICD10Model.icd10.ilike("%{}%".format(args["keyword"]))
                | ICD10Model.description.ilike("%{}%".format(args["keyword"]))
            )
            .limit(10)
            .all()
        )

        icd10s = icd10_schema.dump(icd10s_query)

        # format icd10
        icd10s_with_description = []

        for item in icd10s:
            icd10s_with_description.append(
                f"{item['icd10']}: {item['description']}"
            )

        return icd10s_with_description, 200
