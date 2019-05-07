# https://github.com/dubh3124/Flask-RestPlus-JWT-Mongoengine
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from hivclinic.helpers.custom_converters.date_convertor import DateConverter


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

# config
from hivclinic.config import app_config as Config  # noqa


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.info("Config: %s" % app.config["ENVIRONMENT"])

    """
    # config logging
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s: %(message)s "
        "[in %(pathname)s:%(lineno)d]",
        datefmt="%Y-%m-%d %H:%M%p",
    )
    """

    app.logger.info("Database URI: %s" % app.config["SQLALCHEMY_DATABASE_URI"])

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # add custom url converter
    app.url_map.converters["date"] = DateConverter

    # models
    from hivclinic.models.patient_model import PatientModel  # noqa
    from hivclinic.models.partner_model import PartnerModel  # noqa
    from hivclinic.models.visit_model import VisitModel  # noqa
    from hivclinic.models.investigation_model import InvestigationModel  # noqa
    from hivclinic.models.appointment_model import AppointmentModel  # noqa
    from hivclinic.models.icd10_model import ICD10Model  # noqa

    # namespaces
    from hivclinic.namespaces import api  # noqa

    api.init_app(app)

    return app
