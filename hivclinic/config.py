"""
Reference from
https://github.com/dubh3124/Flask-RestPlus-JWT-Mongoengine/blob/master/.env_bak
"""

import logging
import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    def __init__(self):
        self.DEBUG = False
        self.TESTING = False
        self.PRODUCTION = False

        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_TOKEN_LOCATION = ["cookies"]
        self.JWT_ACCESS_CSRF_HEADER_NAME = os.getenv(
            "JWT_ACCESS_CSRF_HEADER_NAME"
        )
        self.JWT_COOKIE_CSRF_PROTECT = True
        self.JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN")

        self.LOG_LEVEL = logging.DEBUG
        self.SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI_DEV")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        self.MAX_NUMBER_OF_PATIENT_IN_SEARCH = os.getenv(
            "MAX_NUMBER_OF_PATIENT_IN_SEARCH"
        )
        self.MAX_NUMBER_OF_HOSPITAL_IN_SEARCH = os.getenv(
            "MAX_NUMBER_OF_HOSPITAL_IN_SEARCH"
        )

        self.OVERDUE_VL_MONTHS = int(os.getenv("OVERDUE_VL_MONTHS")) or 12
        self.OVERDUE_FU_MONTHS = int(os.getenv("OVERDUE_FU_MONTHS")) or 12


class ProductionConfig(Config):
    def __init__(self):
        super(ProductionConfig, self).__init__()
        self.ENVIRONMENT = "Production"
        self.PRODUCTION = True
        self.LOG_LEVEL = logging.INFO

        # self.MAIL_SERVER = 'smtp.mandrillapp.com'
        # self.MAIL_PORT = 465
        # self.MAIL_USE_SSL = True
        # self.MAIL_USERNAME = os.getenv('MANDRILL_USERNAME')
        # self.MAIL_PASSWORD = os.getenv('MANDRILL_APIKEY')

        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            "SQLALCHEMY_DATABASE_URI_PROD"
        )


class DevelopmentConfig(Config):
    """
    Use "if app.debug" anywhere in your code,
    that code will run in development mode.
    """

    def __init__(self):
        super(DevelopmentConfig, self).__init__()
        self.ENVIRONMENT = "Development"
        self.DEBUG = True
        self.TESTING = False


class TestingConfig(Config):
    """
    A Config to use when we are running tests.
    """

    def __init__(self):
        super(TestingConfig, self).__init__()
        self.ENVIRONMENT = "Testing"
        self.DEBUG = False
        self.TESTING = True

        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            "SQLALCHEMY_DATABASE_URI_TESTING"
        )


environment = os.getenv("FLASK_ENV").lower()

if environment == "testing":
    app_config = TestingConfig()
elif environment == "production":
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()
