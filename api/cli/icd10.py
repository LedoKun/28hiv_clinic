import json
import sys

from api import db
from api.models import ICD10Model


def register(app):
    @app.cli.group()
    def icd10():
        """
        ICD10 related commands
        """
        pass

    @icd10.command()
    def init():
        """
        Init icd10 database
        """
        with open("./api/utils/icd10.json") as f:
            icd10_dict = json.load(f)

        is_table_empty = not bool(ICD10Model.query.first())

        if is_table_empty:
            for icd10_entry in icd10_dict:
                print("Adding: " + icd10_entry["icd10WithDescription"], file=sys.stdout)

                icd10 = ICD10Model()
                icd10.icd10WithDescription = icd10_entry["icd10WithDescription"]
                db.session.add(icd10)

            db.session.commit()
