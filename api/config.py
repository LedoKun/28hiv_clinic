import os

from dotenv import load_dotenv

# load env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    TRAP_HTTP_EXCEPTIONS = os.environ.get("TRAP_HTTP_EXCEPTIONS")

    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_BLACKLIST_ENABLED = os.environ.get("JWT_BLACKLIST_ENABLED")

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get(
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    )

    BCRYPT_ROUNDS = os.environ.get("BCRYPT_ROUNDS")
    DEFAULT_USER = os.environ.get("DEFAULT_USER")
    DEFAULT_PASSWORD = os.environ.get("DEFAULT_PASSWORD")

    PATIENTS_PER_PAGE = os.environ.get("PATIENTS_PER_PAGE")
