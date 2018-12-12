from api.data import bp_api
from api.data.all_patients import AllPatients
# from api.data.tables import Tables

bp_api.add_resource(
    AllPatients, "/all_patients"
)

# bp_api.add_resource(
#     Tables, "/stats"
# )
