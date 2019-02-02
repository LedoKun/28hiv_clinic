from flask import current_app, jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from api.models import PatientModel
from api.schemas import PatientSchema

page_args = {"page_number": fields.Int(missing=0)}


class AllPatients(Resource):
    @jwt_required
    @use_args(page_args)
    def get(self, page_args):
        page_number = page_args["page_number"]
        patients_per_page = int(current_app.config["PATIENTS_PER_PAGE"])
        patients = PatientModel.query.order_by(PatientModel.cid).paginate(
            page_number, patients_per_page, False
        )

        patient_schema = PatientSchema(
            many=True,
            exclude=["visits", "investigation", "appointments"],
            only=[
                "hn",
                "cid",
                "name",
                "dob",
                "sex",
                "marital",
                "gender",
                "nationality",
                "payer",
            ],
        )
        patients.items = patient_schema.dump(patients.items).data
        return jsonify(patients)
