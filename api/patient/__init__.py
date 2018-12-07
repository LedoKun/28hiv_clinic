from flask import Blueprint
from flask_restful import Api


bp = Blueprint("patient", __name__)
bp_api = Api(bp)

from api.patient import routes  # noqa:
