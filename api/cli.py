import json
import sys

import click

from api import db
from api.models import UserModel, icd10Model
from api.schemas import UserSchema
from marshmallow import pprint


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

        is_table_empty = not bool(icd10Model.query.first())

        if is_table_empty:
            for icd10_entry in icd10_dict:
                print(
                    "Adding: " + icd10_entry["icd10WithDescription"],
                    file=sys.stdout,
                )

                icd10 = icd10Model()
                icd10.icd10WithDescription = icd10_entry[
                    "icd10WithDescription"
                ]
                db.session.add(icd10)

            db.session.commit()

    @app.cli.group()
    def user():
        """
        User related commands
        """
        pass

    @user.command()
    @click.argument("username")
    @click.argument("password")
    def add(username, password):
        """
        Add user via command-line interface
        """

        user_schema = UserSchema()
        credential = user_schema.load(
            {"username": username, "password": password}
        ).data

        credential["password"] = UserModel.generate_hash(
            credential["password"]
        )

        new_user = UserModel(**credential)
        db.session.add(new_user)
        db.session.commit()

        print("New user added!", file=sys.stdout)

    @user.command()
    @click.argument("username")
    def delete(username):
        """
        Delete user via command-line interface
        """

        user = UserModel.query.filter(UserModel.username == username).first()

        if user is None:
            print("No user found!", file=sys.stdout)
            return

        db.session.delete(user)
        db.session.commit()

        print("User deleted!", file=sys.stdout)

    @user.command()
    def list_user():
        """
        Loist all  users via command-line interface
        """

        users = UserModel.query.all()

        user_schema = UserSchema(only=["id", "username"], many=True)
        users_data = user_schema.dump(users).data

        pprint(users_data)
