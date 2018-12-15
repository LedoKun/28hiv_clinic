from flask import abort

from api import jwt
from api.models import RevokedTokenModel


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token["jti"]
    return RevokedTokenModel.is_jti_blacklisted(jti)


# Using the expired_token_loader decorator, we will now call
# this function whenever an expired but otherwise valid access
# token attempts to access an endpoint
@jwt.expired_token_loader
def expired_token_callback():
    abort(401)
