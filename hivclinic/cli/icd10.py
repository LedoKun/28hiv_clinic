from hivclinic.models.icd10_model import ICD10Model
from hivclinic import db
import json
from flask import current_app


def register(app):
    @app.cli.group()
    def icd10():
        """ICD10 related commands."""
        pass

    @icd10.command()
    def drop():
        """Drop icd10 database"""
        if not current_app.config["PRODUCTION"]:
            current_app.logger.warn(
                "{} table dropped.".format(ICD10Model.__table__)
            )
            ICD10Model.__table__.drop(db.engine)

        else:
            current_app.logger.error(
                "This function only works in developent/testing mode only."
            )

    @icd10.command()
    def init():
        """ Init ICD10 database """
        with open("./hivclinic/data/icd10.json") as file:
            icd10_dict = json.load(file)

        if not bool(ICD10Model.query.first()):
            for icd10_entry in icd10_dict:
                current_app.logger.info(
                    "Importing ICD10 -- {}".format(icd10_entry["icd10"])
                )

                icd10 = ICD10Model(**icd10_entry)
                db.session.add(icd10)

            db.session.commit()

        else:
            current_app.logger.error("Table is not empty, abort ICD10 import.")
