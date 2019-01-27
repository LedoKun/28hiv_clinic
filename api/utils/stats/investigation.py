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
        df_data = self.df_cleaned[["date", "patient_id", "cd4"]]
        df_data.dropna(subset=["cd4"], inplace=True, how="any")

        # resort the value
        if isInit:
            df_data.sort_values("date", ascending=False, inplace=True)

        # keep only last cd4 info per patient
        df_data = df_data.drop_duplicates(
            subset=["patient_id"], keep="last"
        )

        # bins and labels
        bins = np.array([0, 50, 100, 200, 5000])
        labels = ["0 - 50", "51 - 100", "101 - 200", "> 201"]

        df_data.loc[:, "bins"] = pd.cut(
            df_data.loc[:, "cd4"], bins, labels=labels
        )
        df_binned_cd4 = df_data.groupby(df_data["bins"]).count()

        # only select one column
        df_binned_cd4 = df_binned_cd4[["patient_id"]]

        # rename columns
        df_binned_cd4.columns = ["จำนวน"]
        df_binned_cd4.index.names = ["CD4"]

        return df_binned_cd4
