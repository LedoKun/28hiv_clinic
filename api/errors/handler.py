"""
JSON Error Handlers
Replace default error handlers with JSON equivalents
Add additional error handlers as needed
"""

from api.errors import bp
from werkzeug.exceptions import HTTPException
from flask.json import jsonify
from webargs.flaskparser import parser


# @bp.app_errorhandler(Exception)
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


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_parse_error(error, req, schema):
    error_handler(error)
