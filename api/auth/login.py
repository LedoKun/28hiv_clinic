from flask import abort, jsonify, request
from flask_restful import Resource
from webargs.flaskparser import parser

from api.models import UserModel
from api.schemas import UserSchema
from flask_jwt_extended import create_access_token, create_refresh_token


class Login(Resource):
    def post(self):
        args = parser.parse(UserSchema, request)

        if not args:
            abort(422)

        user = UserModel.query.filter(
            UserModel.username == args["username"]
        ).first()

        if not user:
            abort(401)

        if UserModel.verify_hash(args["password"], user.password):
            access_token = create_access_token(identity=args["username"])
            refresh_token = create_refresh_token(identity=args["username"])

            return jsonify(
                {
                    "message": "OK",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            )

        else:
            abort(401)
