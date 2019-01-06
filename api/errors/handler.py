"""
JSON Error Handlers
Replace default error handlers with JSON equivalents
Add additional error handlers as needed
"""

from api.errors import bp
from werkzeug.exceptions import HTTPException
from webargs.core import ValidationError
from flask.json import jsonify
from webargs.flaskparser import parser
import sys


@bp.app_errorhandler(Exception)
def error_handler(error):
    """
    Standard Error Handler
    """

    print(error, file=sys.stdout)

    if isinstance(error, HTTPException):
        error_payload = {
            "statusCode": error.code,
            "name": error.name,
            "description": error.description,
        }

    elif isinstance(error, ValidationError):
        error_payload = {
            "statusCode": error.status_code,
            "name": "Form Validation Error",
            "description": str(error),
        }

    else:
        error_payload = {
            "statusCode": 500,
            "name": "Internal Server Error",
            "description": str(error),
        }

    return (jsonify(error_payload), error_payload["statusCode"])


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_parse_error(error, req, schema):
    error_handler(error)
