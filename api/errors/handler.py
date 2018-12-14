"""
JSON Error Handlers
Replace default error handlers with JSON equivalents
Add additional error handlers as needed
"""

from api.errors import bp
from werkzeug.exceptions import HTTPException
from flask.json import jsonify, abort
from webargs.flaskparser import parser
from flask import abort
from jwt.exceptions import ExpiredSignatureError


# This error handler is necessary for usage with Flask-RESTful
# @parser.error_handler
# def handle_request_parsing_error(error, req, schema):
#     error_handler(error)
@parser.error_handler
def handle_parse_error(error, req, schema):
    fields, description = (
        str(getattr(error, "fields", "No Field Specified")),
        str(getattr(error, "message", "Invalid Request")),
    )

    error_payload = {
        "statusCode": 422,
        "name": "Data Validation Failed.",
        "fields": fields,
        "description": description,
    }

    import sys

    print(error_payload, file=sys.stdout)

    return abort(422)


@bp.app_errorhandler(Exception)
def error_handler(error):
    """
    Standard Error Handler
    """

    if isinstance(error, HTTPException):
        error_payload = {
            "statusCode": error.code,
            "name": error.name,
            "description": error.description,
        }

        return (jsonify(error_payload), error.code)

    elif isinstance(ExpiredSignatureError):
        abort(401)

    else:
        return (
            jsonify(
                {
                    "statusCode": 500,
                    "name": "Internal Server Error",
                    "description": str(error),
                }
            ),
            500,
        )
