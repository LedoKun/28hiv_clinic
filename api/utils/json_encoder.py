import datetime

from flask.json import JSONEncoder
from flask import current_app

from flask_sqlalchemy import Pagination
from pandas import DataFrame, Series

# import json


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

        # if isinstance(o, (DataFrame, Series)):
        #     if isinstance(o, Series):
        #         o = o.to_frame()

        #     o = o.reset_index()

        #     return json.loads(o.to_json(orient='split', default_handler=str))

        # if isinstance(o, DataFrame):
        #     return json.loads(o.to_json(orient="split", default_handler=str))

        # if isinstance(o, Series):
        #     return json.loads(o.to_json(default_handler=str))

        if isinstance(o, DataFrame):
            classes = current_app.config["STATS_TABLE_CLASSES"]
            o.fillna(value="-", inplace=True)

            return o.to_html(
                classes=classes,
                escape=True,
                bold_rows=False,
                border=0
            )

        if isinstance(o, Series):
            classes = current_app.config["STATS_TABLE_CLASSES"]
            o.fillna(value="-", inplace=True)

            return o.to_frame().to_html(
                classes=classes,
                escape=True,
                bold_rows=False,
                border=0
            )

        return super().default(o)
