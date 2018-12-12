from flask import abort, jsonify, request
from flask_restful import Resource
from webargs.flaskparser import parser

from api import db
from api.models import PatientModel
from api.schemas import PatientSchema
from flask_jwt_extended import jwt_required


class PatientHandler(Resource):
    @jwt_required
    def get(self, hn):
        if not hn:
            abort(422)

        patient = PatientModel.query.filter(PatientModel.hn == hn).first()

        patient_schema = PatientSchema()
        return patient_schema.dump(patient).data

    @jwt_required
    def put(self):
        args = parser.parse(PatientSchema, request)
        patient = PatientModel.query.filter(
            PatientModel.hn == args["hn"]
        ).first()

        if patient is None:
            # Insert new data
            patient = PatientModel(**args)

        else:
            # Update data
            patient.update(**args)

        db.session.add(patient)
        db.session.commit()

        return jsonify({"message": "OK"})

    @jwt_required
    def delete(self, hn):
        if not hn:
            abort(422)

        patient = PatientModel.query.filter(PatientModel.hn == hn).first()

        if patient is None:
            abort(422)

        db.session.delete(patient)
        db.session.commit()
