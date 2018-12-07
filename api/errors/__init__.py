from flask import Blueprint
from flask_restful import Api


bp = Blueprint("errors", __name__)
bp_api = Api(bp)

from api.errors import handler  # noqa
