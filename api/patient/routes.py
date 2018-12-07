from api.patient import bp_api
from api.patient.patient_handler import PatientHandler
from api.patient.child_handler import ChildHandler
from api.patient.dashboard import Dashboard

bp_api.add_resource(PatientHandler, "/", "/<string:hn>", strict_slashes=False)
bp_api.add_resource(
    ChildHandler,
    "/<string:hn>/<string:child_type>",
    "/<string:hn>/<string:child_type>/<string:child_id>",
    strict_slashes=False,
)
bp_api.add_resource(Dashboard, "/dashboard")
