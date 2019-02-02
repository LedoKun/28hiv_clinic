from flask import Flask
from api.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import pandas as pd


# default='warn'
pd.options.mode.chained_assignment = None

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # register JWT blacklist checker
    import api.jwt  # noqa

    # Register errors handlers
    import api.errors  # noqa

    # Register buleprints
    from api.patient import bp as patient_bp  # noqa
    from api.search import bp as search_bp  # noqa
    from api.errors import bp as error_bp  # noqa
    from api.auth import bp as auth_bp  # noqa
    from api.data import bp as data_bp  # noqa

    app.register_blueprint(error_bp)
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(patient_bp, url_prefix="/patient")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(data_bp, url_prefix="/data")

    # Custom JSON Encoder
    from api.utils.json_encoder import JSONEncoder  # noqa

    app.json_encoder = JSONEncoder

    return app
