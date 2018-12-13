from flask import jsonify, request
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import parser

from api import db
from api.models import AppointmentModel, PatientModel, VisitModel
from api.schemas import AppointmentSchema, VisitSchema
from flask_jwt_extended import jwt_required

today_args = {"date": fields.Date(required=True)}


class Dashboard(Resource):
    @jwt_required
    def get(self):
        args = parser.parse(today_args, request)
        selected_date = args["date"]

        # today_appointment
        today_appointment = (
            AppointmentModel.query.filter(AppointmentModel.date == selected_date)
            .order_by(AppointmentModel.id)
            .all()
        )

        appointment_schema = AppointmentSchema(
            only=["date", "appointmentFor", "patient.hn", "patient.name"], many=True
        )

        today_appointment = appointment_schema.dump(today_appointment).data

        # patientExamined
        patient_examined = (
            VisitModel.query.filter(VisitModel.date == selected_date)
            .order_by(VisitModel.modify_timestamp)
            .all()
        )

        visit_schema = VisitSchema(
            only=["date", "impression", "patient.hn", "patient.name"], many=True
        )

        patient_examined = visit_schema.dump(patient_examined).data

        # count total number of patients
        count_patient = db.session.query(PatientModel.id).count()

        # data for the frontend
        dashboard_data = {
            "todayAppointment": today_appointment,
            "patientExamined": patient_examined,
            "countPatient": count_patient,
        }

        return jsonify(dashboard_data)
