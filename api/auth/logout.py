from flask import jsonify
from flask_jwt_extended import get_jti, jwt_required
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from api import db
from api.models import RevokedTokenModel

logout_args = {
    "jwt_token": fields.Str(required=True),
    "jwt_refresh_token": fields.Str(required=True),
}


class Logout(Resource):
    @jwt_required
    @use_args(logout_args)
    def delete(self, args):
        access_jti = get_jti(args["jwt_token"])
        refresh_jti = get_jti(args["jwt_refresh_token"])

        if bool(access_jti):
            revoked_access_token = RevokedTokenModel(jti=access_jti)
            db.session.add(revoked_access_token)

        if bool(refresh_jti):
            revoked_refresh_token = RevokedTokenModel(jti=refresh_jti)
            db.session.add(revoked_refresh_token)

        if bool(access_jti) or bool(refresh_jti):
            db.session.commit()

        return jsonify({"message": "OK"})
