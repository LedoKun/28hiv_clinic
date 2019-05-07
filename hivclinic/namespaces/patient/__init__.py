from flask_restplus import Namespace

api = Namespace("patient", description="patient related operations")

from . import patient_resource  # noqa
from . import subcollection_resource  # noqa
from . import visit_appointment_resource  # noqa
from . import visit_appointment_resource  # noqa
