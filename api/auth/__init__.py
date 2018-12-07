from flask import Blueprint
from flask_restful import Api


bp = Blueprint("auth", __name__)
bp_api = Api(bp)

from api.auth import routes  # noqa:
