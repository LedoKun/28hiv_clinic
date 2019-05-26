from flask_restplus import Namespace

api = Namespace("form_helpers", description="forms related operations")

from . import form_helpers_resource  # noqa
