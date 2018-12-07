from flask import Blueprint
from flask_restful import Api


bp = Blueprint("search", __name__)
bp_api = Api(bp)

from api.search import routes  # noqa:
