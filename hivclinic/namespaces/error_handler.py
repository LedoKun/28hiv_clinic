from flask import abort, current_app
from . import api
from marshmallow.exceptions import ValidationError
from webargs.flaskparser import parser
from sqlalchemy.exc import IntegrityError


@api.errorhandler
def default_handler(error):
    """Default error handler"""
    if isinstance(error, ValidationError):
        current_app.logger.error(
            "Form validation error.", exc_info=current_app.config["DEBUG"]
        )

        return abort(422, error.messages)

    elif isinstance(error, IntegrityError):
        current_app.logger.error(
            "Duplicated key detected", exc_info=current_app.config["DEBUG"]
        )
        return abort(409, "Duplicated key detected.")

    else:
        current_app.logger.error(
            "Internal server error - {}".format(str(error)),
            exc_info=current_app.config["DEBUG"],
        )
        return abort(500, "Internal server error.")


@parser.error_handler
def paeser_error_handler(error, req, schema, error_status_code, error_headers):
    current_app.logger.error("Form submission with validation error detected.")

    if current_app.config["DEBUG"]:
        current_app.logger.error(
            "{} --- {} --- {}".format(str(error), str(req), str(schema)),
            exc_info=current_app.config["DEBUG"],
        )

    default_handler(error)
