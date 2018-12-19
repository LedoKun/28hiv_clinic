from flask import abort, current_app, jsonify, request
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import parser

from api import db
from api.models import AppointmentModel, PatientModel, VisitModel
from api.schemas import AppointmentSchema, VisitSchema
from flask_jwt_extended import jwt_required

today_args = {
    "date": fields.Date(required=True),
    "appointment_page_number": fields.Int(missing=0),
    "examined_page_number": fields.Int(missing=0),
}


class Dashboard(Resource):
    @jwt_required
    def get(self):
        args = parser.parse(today_args, request)

        if not args:
            abort(422)

        selected_date = args["date"]

        # number of items shown per page
        appointment_per_page = int(
            current_app.config["DASHBOARD_APPOINTMENT_PER_PAGE"]
        )
        examined_per_page = int(
            current_app.config["DASHBOARD_EXAMINED_PER_PAGE"]
        )

        # today_appointment
        today_appointment = (
            AppointmentModel.query.filter(
                AppointmentModel.date == selected_date
            )
            .order_by(AppointmentModel.id)
            .paginate(
                args["appointment_page_number"], appointment_per_page, False
            )
        )

        appointment_schema = AppointmentSchema(
            only=[
                "date",
                "appointmentFor",
                "patient.hn",
                "patient.cid",
                "patient.name",
                "patient.tel",
                "patient.relative_tel",
            ],
            many=True,
        )

        today_appointment.items = appointment_schema.dump(
            today_appointment.items
        ).data

        # patientExamined
        patient_examined = (
            VisitModel.query.filter(VisitModel.date == selected_date)
            .order_by(VisitModel.modify_timestamp)
            .paginate(args["examined_page_number"], examined_per_page, False)
        )

        visit_schema = VisitSchema(
            only=[
                "date",
                "impression",
                "patient.hn",
                "patient.cid",
                "patient.name",
            ],
            many=True,
        )

        patient_examined.items = visit_schema.dump(
            patient_examined.items
        ).data

        # count total number of patients
        count_patient = db.session.query(PatientModel.id).count()

        # data for the frontend
        dashboard_data = {
            "todayAppointment": today_appointment,
            "patientExamined": patient_examined,
            "countPatient": count_patient,
        }

        return jsonify(dashboard_data)
