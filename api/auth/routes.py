from api.auth import bp_api
from api.auth.login import Login
from api.auth.logout import Logout


bp_api.add_resource(Login, "/login")
bp_api.add_resource(Logout, "/logout")
