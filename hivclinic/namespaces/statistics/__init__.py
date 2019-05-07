from flask_restplus import Namespace

api = Namespace("statistics", description="statistics related operations")

from . import statistics_resource  # noqa
