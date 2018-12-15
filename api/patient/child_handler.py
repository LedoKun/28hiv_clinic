from flask import abort, jsonify, request
from flask_restful import Resource
from webargs.flaskparser import parser

from api import db
from api.models import (
    AppointmentModel,
    InvestigationModel,
    PatientModel,
    VisitModel,
)
from api.schemas import AppointmentSchema, InvestigationSchema, VisitSchema
from flask_jwt_extended import jwt_required


class ChildHandler(Resource):
    @staticmethod
    def getModelAndSchema(child_type):
        if child_type == "visit":
            return VisitModel, VisitSchema

        elif child_type == "investigation":
            return InvestigationModel, InvestigationSchema

        elif child_type == "appointment":
            return AppointmentModel, AppointmentSchema

        return None, None

    @jwt_required
    def get(self, hn, child_type):
        if not hn:
            abort(422)

        else:
            hn = str(hn).replace("_", "/")

        # find patient id
        patient = PatientModel.query.filter(PatientModel.hn == hn).first()

        if patient is None:
            abort(422)

        # get schema and model
        model_object, schema_object = ChildHandler.getModelAndSchema(
            child_type
        )

        # get child data
        if child_type == "visit":
            child_data = patient.visits

        elif child_type == "investigation":
            child_data = patient.investigation

        elif child_type == "appointment":
            child_data = patient.appointments

        else:
            child_data = None

        if child_data is None:
            return jsonify([])

        # serialize model
        child_schema = schema_object(many=True)
        child_data = child_schema.dump(child_data).data

        return jsonify(child_data)

    @jwt_required
    def put(self, hn, child_type):
        # get schema and model
        model_object, schema_object = ChildHandler.getModelAndSchema(
            child_type
        )

        args = parser.parse(schema_object, request, locations=["json"])

        # find patient id
        if not hn or not args:
            abort(422)

        else:
            hn = str(hn).replace("_", "/")

        patient = PatientModel.query.filter(PatientModel.hn == hn).first()

        if patient is None:
            abort(422)

        # insert new data
        child_data = model_object(**args)
        child_data.patient_id = patient.id

        db.session.add(child_data)
        db.session.commit()

        return jsonify({"message": "OK"})

    @jwt_required
    def delete(self, hn, child_type, child_id):
        if not child_id:
            abort(422)

        # get schema and model
        model_object, schema_object = ChildHandler.getModelAndSchema(
            child_type
        )

        # delete data in table
        child_data = model_object.query.filter(
            model_object.id == child_id
        ).first()

        if child_data is None:
            abort(422)

        db.session.delete(child_data)
        db.session.commit()

        return jsonify({"message": "OK"})
