from flask import abort, jsonify
from flask_restful import Resource
from webargs.flaskparser import use_args

from api import db
from api.models import UserModel
from api.schemas import UserSchema
from flask_jwt_extended import jwt_required


class CreateUser(Resource):
    @classmethod
    def user_exists(username):
        return (
            UserModel.query.filter(UserModel.username == username).first()
            is not None
        )

    @use_args(UserSchema)
    @jwt_required
    def post(self, args):
        if CreateUser.user_exists(args["username"]):
            abort(409)

        # insert new data
        new_credential = {
            "username": args["username"],
            "password": UserModel.generate_hash(args["password"]),
        }
        new_user = UserModel(**new_credential)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "OK"})
