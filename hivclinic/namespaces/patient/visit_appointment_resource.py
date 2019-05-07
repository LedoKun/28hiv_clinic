from flask_restplus import Resource

from hivclinic import db
from hivclinic.models.appointment_model import AppointmentModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.models.visit_model import VisitModel
from hivclinic.schemas.appointment_schema import AppointmentSchema
from hivclinic.schemas.patient_schema import PatientSchema

from . import api


@api.route("/appointment/<date:appointmentDate>")
class SearchAppointmentResource(Resource):
    @api.doc("list_all_appointments")
    def get(self, appointmentDate):
        """List all appointments"""
        only = [
            "appointmentFor",
            "patient.id",
            "patient.hn",
            "patient.clinicID",
            "patient.name",
        ]

        appointment_schema = AppointmentSchema(many=True, only=only)

        query = (
            db.session.query(AppointmentModel)
            .join(PatientModel)
            .order_by(PatientModel.clinicID)
            .filter(AppointmentModel.date == appointmentDate)
        )

        appointments = appointment_schema.dump(query)

        return appointments, 200


@api.route("/visit/<date:visitDate>")
class SearchVisitResource(Resource):
    @api.doc("list_all_visits")
    def get(self, visitDate):
        """List all appointments"""
        only = ["id", "hn", "clinicID", "name"]

        patient_schema = PatientSchema(many=True, only=only)

        patients_query = (
            db.session.query(PatientModel)
            .join(VisitModel)
            .order_by(PatientModel.clinicID)
            .filter(VisitModel.date == visitDate)
        )

        patients = patient_schema.dump(patients_query)

        return patients, 200
