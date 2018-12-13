from flask import abort, jsonify
from flask_restful import Resource

from api.models import RevokedTokenModel
from flask_jwt_extended import (
    jwt_required,
    get_raw_jwt,
    jwt_refresh_token_required,
)
from api import db


class Logout(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()["jti"]

        if not bool(jti):
            abort(400)

        revoked_token = RevokedTokenModel(jti=jti)
        db.session.add(revoked_token)
        db.session.commit()

        return jsonify({"message": "OK"})


class LogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()["jti"]

        if not bool(jti):
            abort(400)

        revoked_token = RevokedTokenModel(jti=jti)
        db.session.add(revoked_token)
        db.session.commit()
        return {"message": "OK"}
