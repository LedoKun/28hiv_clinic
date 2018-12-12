from flask import Blueprint
from flask_restful import Api


bp = Blueprint("data", __name__)
bp_api = Api(bp)

from api.data import routes  # noqa:
