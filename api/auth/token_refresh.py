from flask import jsonify
from flask_jwt_extended import (create_access_token, get_jwt_identity,
                                jwt_refresh_token_required)
from flask_restful import Resource


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return jsonify({"message": "OK", "access_token": access_token})
