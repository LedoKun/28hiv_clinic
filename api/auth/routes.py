from api.auth import bp_api
from api.auth.login import Login
from api.auth.logout import Logout
from api.auth.token_refresh import TokenRefresh


bp_api.add_resource(Login, "/login")
bp_api.add_resource(Logout, "/logout")
bp_api.add_resource(TokenRefresh, "/token_refresh")
