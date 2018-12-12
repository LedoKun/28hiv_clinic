import datetime
from flask.json import JSONEncoder
from flask_sqlalchemy import Pagination


class JSONEncoder(JSONEncoder):
    """
    Extend json-encoder class
    """

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return str(o)

        if isinstance(o, Pagination):
            return {
                "has_next": o.has_next,
                "has_prev": o.has_prev,
                "items": o.items,
                "next_num": o.next_num,
                "page": o.page,
                "pages": o.pages,
                "per_page": o.per_page,
                "prev_num": o.prev_num,
                "total": o.total,
            }

        return super().default(o)
