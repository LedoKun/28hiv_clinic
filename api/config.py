import os

from dotenv import load_dotenv

# load env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    # Must be set to True
    PROPAGATE_EXCEPTIONS = True
    TRAP_HTTP_EXCEPTIONS = os.environ.get("TRAP_HTTP_EXCEPTIONS") or False

    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_BLACKLIST_ENABLED = os.environ.get("JWT_BLACKLIST_ENABLED") or True

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH")) or 16777216

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = (
        os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS") or False
    )

    BCRYPT_ROUNDS = os.environ.get("BCRYPT_ROUNDS") or 8

    PATIENTS_PER_PAGE = os.environ.get("PATIENTS_PER_PAGE") or 20
    DASHBOARD_APPOINTMENT_PER_PAGE = (
        os.environ.get("DASHBOARD_APPOINTMENT_PER_PAGE") or 20
    )
    DASHBOARD_EXAMINED_PER_PAGE = (
        os.environ.get("DASHBOARD_EXAMINED_PER_PAGE") or 20
    )

    STATS_TABLE_CLASSES = os.environ.get("STATS_TABLE_CLASSES").split(
        ","
    ) or "table,is-fullwidth,is-striped,is-narrow".split(",")
