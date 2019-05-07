from flask import abort, request

from flask_restplus import Resource
from hivclinic import db

# all models
from hivclinic.models.visit_model import VisitModel
from hivclinic.models.appointment_model import AppointmentModel
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.partner_model import PartnerModel
from hivclinic.models.patient_model import PatientModel

# all schemas
# from hivclinic.schemas.patient_schema import PatientSchema
from hivclinic.schemas.visit_schema import VisitSchema
from hivclinic.schemas.appointment_schema import AppointmentSchema
from hivclinic.schemas.investigation_schema import InvestigationSchema
from hivclinic.schemas.partner_schema import PartnerSchema

from webargs.flaskparser import parser

from . import api
import uuid


def getSubcollectionClasses(type):
    if type == "partners":
        return PartnerModel, PartnerSchema

    elif type == "visits":
        return VisitModel, VisitSchema

    elif type == "investigations":
        return InvestigationModel, InvestigationSchema

    elif type == "appointments":
        return AppointmentModel, AppointmentSchema

    else:
        abort(400, "Invalid subcollection type.")


def convert_uuid_to_str(data):
    # Flas-Restplus's json encoder does not
    # seem to handle UUID as ForeignKey very well
    if isinstance(data, list):
        for element in data:
            convert_uuid_to_str(element)

    elif isinstance(data, dict):
        for key, item in data.items():
            if isinstance(item, uuid.UUID):
                data[key] = str(item)

    return data


@api.route("/<uuid:patient_uuid>/<string:subcollection_type>")
@api.param("patient_uuid", "The patient identifier")
@api.param("subcollection_type", "The subcollection type")
class AllSubcollectionResource(Resource):
    @api.doc("list_all_subcollection")
    def get(self, patient_uuid, subcollection_type):
        """List all subcollections associated with the patient with the UUID"""
        Model, Schema = getSubcollectionClasses(subcollection_type)
        subcollection_schema = Schema(many=True)

        subcollection = Model.query.filter_by(patientID=patient_uuid).all()
        subcollection = subcollection_schema.dump(subcollection)
        subcollection = convert_uuid_to_str(subcollection)

        return subcollection, 200

    @api.doc("add_new_subcollection")
    def post(self, patient_uuid, subcollection_type):
        """Add a new subcollection associated with the patient with the UUID"""
        _, Schema = getSubcollectionClasses(subcollection_type)
        subcollection_schema = Schema()

        patient = PatientModel.query.filter_by(id=patient_uuid).first()

        if patient is None:
            abort(404, "Patient not found.")

        subcollection_payload = parser.parse(Schema, request)
        subcollection = getattr(patient, subcollection_type)
        subcollection.append(subcollection_payload)
        db.session.commit()

        subcollection = subcollection_schema.dump(subcollection_payload)
        subcollection = convert_uuid_to_str(subcollection)

        return subcollection, 200


@api.route(
    "/<uuid:patient_uuid>/<string:subcollection_type>"
    "/<uuid:subcollection_uuid>"
)
@api.param("patient_uuid", "The patient identifier")
@api.param("subcollection_type", "The subcollection type")
@api.param("subcollection_uuid", "The subcollection UUID")
class SubcollectionResource(Resource):
    @api.doc("get_patient")
    def get(self, patient_uuid, subcollection_type, subcollection_uuid):
        """Get a subcollection associated with the patient with the UUID"""
        Model, Schema = getSubcollectionClasses(subcollection_type)
        subcollection_schema = Schema(many=False)

        subcollection = (
            Model.query.filter_by(id=subcollection_uuid)
            .filter_by(patientID=patient_uuid)
            .first()
        )
        subcollection = subcollection_schema.dump(subcollection)
        subcollection = convert_uuid_to_str(subcollection)

        return subcollection, 200

    @api.doc("patch_subcollection")
    def patch(self, patient_uuid, subcollection_type, subcollection_uuid):
        """Patch subcollection with the UUID"""
        Model, Schema = getSubcollectionClasses(subcollection_type)
        subcollection_schema = Schema(many=False)

        patient_payload = parser.parse(Schema, request)
        patient_payload = subcollection_schema.dump(patient_payload)

        subcollection = (
            Model.query.filter_by(id=subcollection_uuid)
            .filter_by(patientID=patient_uuid)
            .first()
        )

        if subcollection is None:
            abort(404, "Patient not found.")

        subcollection.update(**patient_payload)

        db.session.add(subcollection)
        db.session.commit()

        subcollection = subcollection_schema.dump(subcollection)
        subcollection = convert_uuid_to_str(subcollection)

        return subcollection, 200

    @api.doc("delete_existing_subcollection")
    def delete(self, patient_uuid, subcollection_type, subcollection_uuid):
        """Delete subcollection with the UUID"""
        Model, _ = getSubcollectionClasses(subcollection_type)

        subcollection = (
            Model.query.filter_by(id=subcollection_uuid)
            .filter_by(patientID=patient_uuid)
            .first()
        )

        if subcollection:
            subcollection.deleted = True

            db.session.add(subcollection)
            db.session.commit()

        return None, 204
