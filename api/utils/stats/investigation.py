from api import db
from api.models import InvestigationModel
import pandas as pd
import numpy as np


class IxStats:
    df_raw = None
    df_cleaned = None

    def __init__(self):
        self.df_raw = pd.io.sql.read_sql(
            sql=InvestigationModel.query.statement, con=db.session.bind
        )

        self.df_raw["date"] = pd.to_datetime(
            self.df_raw["date"], errors="coerce"
        )

        self.df_raw.set_index("date")
        self.df_raw.sort_values("date", ascending=True, inplace=True)
        self.df_cleaned = self.df_raw.fillna(value="N/A")

    def getCD4(self, isInit=False):
        bins = np.array([50, 100, 200, 5000])
        df_data = self.df_cleaned

        if isInit:
            df_data.sort_values("date", ascending=False, inplace=True)

        # keep only last cd4 info per patient
        df_data.dropna(subset=["cd4"])
        self.df_last = self.df_cleaned.drop_duplicates(
            subset=["patient_id"], keep="last"
        )

        df_groupby_cd4 = (
            df_data.groupby(["cd4", pd.cut(df_data.cd4, bins)])
            .size()
            .unstack()
        )

        # sort columns' name
        df_groupby_cd4.sort_index(axis=1, inplace=True)

        # rename columns
        df_groupby_cd4.columns.rename("จำนวน", inplace=True)
        df_groupby_cd4.index.names = ["CD4"]

        return df_groupby_cd4
