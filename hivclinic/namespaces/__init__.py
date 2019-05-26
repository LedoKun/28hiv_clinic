from flask_restplus import Api

from hivclinic.namespaces.patient import api as patient_api
from hivclinic.namespaces.statistics import api as statistics_api
from hivclinic.namespaces.form_helpers import api as form_helpers_api

api = Api(
    title="HIV Clinic Backend API",
    version="0.1",
    description="This is an API to be used with HIV Clinic frontend.",
)

api.add_namespace(patient_api, path="/patient")
api.add_namespace(statistics_api, path="/statistics")
api.add_namespace(form_helpers_api, path="/form_helpers")

from . import error_handler  # noqa
