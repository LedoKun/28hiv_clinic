from api import db
from api.models import PatientModel
import pandas as pd
import numpy as np

from datetime import date


class PatientStats:
    df_raw = None
    df_cleaned = None

    def __init__(self):
        self.df_raw = pd.io.sql.read_sql(
            sql=PatientModel.query.statement, con=db.session.bind
        )

        # calculate age
        self.df_raw["age"] = self.df_raw["dob"].apply(
            PatientStats.calculate_age
        )

        self.df_cleaned = self.df_raw.fillna(value="N/A")

    @staticmethod
    def calculate_age(born):
        if isinstance(born, date):
            today = date.today()
            age = (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )

            return age

        else:
            return "-10"

    def filteredNationalities(self, include=[], exclude=[]):
        df_data = self.df_cleaned

        # exclude
        if exclude:
            df_data = df_data.loc[~df_data["nationality"].isin(exclude)]

        # include
        if include:
            df_data = df_data.loc[df_data["nationality"].isin(include)]

        return df_data

    def getAgeSexGenderDF(self, include=[], exclude=[]):
        try:
            bins = np.arange(-10, 110, 10)
            df_data = self.filteredNationalities(
                include=include, exclude=exclude
            )

            df_groupby_age = (
                df_data.groupby(["sex", "gender", pd.cut(df_data.age, bins)])
                .size()
                .unstack()
            )

            # sort columns' name
            df_groupby_age.sort_index(axis=1, inplace=True)

            # rename columns
            df_groupby_age.columns.rename("อายุ", inplace=True)
            df_groupby_age.index.names = ["Sex", "Gender"]

            return df_groupby_age

        except (ValueError, AttributeError):
            return None

    def getPayerDF(self, include=[], exclude=[]):
        try:
            df_data = self.filteredNationalities(
                include=include, exclude=exclude
            )

            series_payer = df_data.groupby(["payer"]).size()

            # rename columns
            df_payer = series_payer.to_frame(name="จำนวน")
            df_payer.index.names = ["สิทธิ์การรักษา"]

            return df_payer

        except (ValueError, AttributeError):
            return None

    def getRefferalDF(self, include=[], exclude=[]):
        try:
            df_data = self.filteredNationalities(
                include=include, exclude=exclude
            )

            df_isRefer = (
                df_data.groupby(["sex", "gender", "isRefer", "referFrom"])
                .size()
                .unstack()
            )

            # sort columns' name
            df_isRefer.sort_index(axis=1, inplace=True)

            # rename columns
            df_isRefer.columns.rename("ส่งตัวจาก", inplace=True)
            df_isRefer.index.names = ["Sex", "Gender", "สถานะการส่งตัว"]

            return df_isRefer

        except (ValueError, AttributeError):
            return None
