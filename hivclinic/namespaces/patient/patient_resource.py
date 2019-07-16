from flask import abort, request, current_app

from flask_restplus import Resource
from hivclinic import db
from hivclinic.models.patient_model import PatientModel
from hivclinic.schemas.patient_schema import PatientSchema
from webargs.flaskparser import parser, use_args
from webargs import fields
from marshmallow.validate import OneOf

from . import api


@api.route("/")
class AllPatientResource(Resource):
    @api.doc("list_all_patients")
    def get(self):
        """List all patients"""
        only = [
            "id",
            "hn",
            "clinicID",
            "governmentID",
            "napID",
            "name",
            "sex",
            "gender",
            "nationality",
            "healthInsurance",
            "dateOfBirth",
            "phoneNumbers",
        ]

        patient_schema = PatientSchema(
            many=True, exclude=PatientModel.relationship_keys, only=only
        )

        patients_query = PatientModel.query.order_by(
            PatientModel.clinicID
        ).all()
        patients = patient_schema.dump(patients_query)

        return patients, 200

    @api.doc("add_new_patient")
    def post(self):
        """Add new patient"""
        patient = parser.parse(PatientSchema, request)

        db.session.add(patient)
        db.session.commit()

        patient_schema = PatientSchema()
        return patient_schema.dump(patient), 200


@api.route("/search")
class SearchPatientResource(Resource):
    @api.doc("search_for_patients")
    @use_args(
        {
            "fieldName": fields.Str(
                required=False,
                validate=OneOf(["referredFrom", "referredOutTo"]),
            ),
            "keyword": fields.Str(required=True),
        },
        locations=("querystring",),
    )
    def get(self, args):
        """Search for patients"""
        if "fieldName" not in args:
            only = ["id", "hn", "clinicID", "name", "nationality"]

            patient_schema = PatientSchema(
                many=True, exclude=PatientModel.relationship_keys, only=only
            )

            patients_query = (
                PatientModel.query.order_by(PatientModel.clinicID)
                .filter(
                    PatientModel.hn.ilike("%{}%".format(args["keyword"]))
                    | PatientModel.clinicID.ilike(
                        "%{}%".format(args["keyword"])
                    )
                    | PatientModel.napID.ilike("%{}%".format(args["keyword"]))
                    | PatientModel.name.ilike("%{}%".format(args["keyword"]))
                )
                .limit(current_app.config["MAX_NUMBER_OF_PATIENT_IN_SEARCH"])
                .all()
            )

        else:
            patient_schema = PatientSchema(
                many=True,
                exclude=PatientModel.relationship_keys,
                only=[args["fieldName"]],
            )

            patients_query = (
                PatientModel.query.filter(
                    getattr(PatientModel, args["fieldName"]).ilike(
                        "%{}%".format(args["keyword"])
                    )
                )
                .limit(current_app.config["MAX_NUMBER_OF_HOSPITAL_IN_SEARCH"])
                .all()
            )

        patients = patient_schema.dump(patients_query)

        return patients, 200


@api.route("/<uuid:patient_uuid>")
@api.param("patient_uuid", "The patient identifier")
class PatientResource(Resource):
    @api.doc("get_patient")
    @use_args(
        {
            "patient_uuid": fields.UUID(location="view_args"),
            "only_dermographic": fields.Boolean(
                location="querystring", missing=False
            ),
        }
    )
    def get(self, args, **kwargs):
        """Get patient with the UUID"""
        if args["only_dermographic"]:
            patient_schema = PatientSchema(
                many=False, exclude=PatientModel.relationship_keys
            )

        else:
            patient_schema = PatientSchema(many=False)

        patient = PatientModel.query.filter_by(id=args["patient_uuid"]).first()

        return patient_schema.dump(patient), 200

    @api.doc("modify_existing_patient")
    def patch(self, patient_uuid):
        """Modify patient with the UUID"""
        patient_schema = PatientSchema(many=False)

        patient_payload = parser.parse(PatientSchema, request)
        patient_payload = patient_schema.dump(patient_payload)

        patient = PatientModel.query.filter_by(id=patient_uuid).first()

        if patient:
            patient.update(**patient_payload)

            db.session.add(patient)
            db.session.commit()

            return patient_schema.dump(patient), 200

        else:
            abort(404, "Patient not found.")

    @api.doc("delete_existing_patient")
    def delete(self, patient_uuid):
        """Delete patient with the UUID"""
        patient = PatientModel.query.filter_by(id=patient_uuid).first()

        if patient:
            patient.deleted = True

            db.session.add(patient)
            db.session.commit()

        return None, 204
