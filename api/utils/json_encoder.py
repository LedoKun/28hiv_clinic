import datetime
from flask.json import JSONEncoder
from api.models import (
    PatientModel,
    VisitModel,
    InvestigationModel,
    AppointmentModel,
)


class JSONEncoder(JSONEncoder):
    """
    Extend json-encoder class
    """

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return str(o)

        if isinstance(
            o,
            (PatientModel, VisitModel, InvestigationModel, AppointmentModel),
        ):
            return o.serialize()

        return super().default(o)
