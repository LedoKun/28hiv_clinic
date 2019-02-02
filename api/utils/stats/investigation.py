import numpy as np
import pandas as pd

from api import db
from api.models import InvestigationModel


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
        try:
            result = {}
            df_data = self.df_cleaned[["date", "patient_id", "cd4"]]
            df_data.dropna(subset=["cd4"], inplace=True, how="any")

            # keep only last or first cd4 info per patient
            if isInit:
                df_data = df_data.drop_duplicates(
                    subset=["patient_id"], keep="first"
                )
                result["header"] = "CD4 Levels Initially"

            else:
                df_data = df_data.drop_duplicates(
                    subset=["patient_id"], keep="last"
                )
                result["header"] = "CD4 Levels Overall"

            # bins and labels
            bins = np.array([-1, 50, 100, 200, 350, 5000])
            labels = ["0 - 50", "51 - 100", "101 - 200", "201 - 350", "> 350"]

            df_data["cd4"] = pd.to_numeric(df_data["cd4"], errors="coerce")
            df_data.loc[:, "bins"] = pd.cut(
                df_data.loc[:, "cd4"], bins, labels=labels
            )
            df_binned_cd4 = df_data.groupby(df_data["bins"]).count()

            # only select one column
            df_binned_cd4 = df_binned_cd4[["patient_id"]]

            # rename columns
            df_binned_cd4.columns = ["จำนวน"]
            df_binned_cd4.index.names = ["CD4"]

            # stats df
            df_stats = pd.DataFrame(df_data["cd4"].describe())
            df_stats.columns = ["ข้อมูล"]

            # results
            result["df_data"] = df_binned_cd4
            result["df_describe"] = df_stats

            return result

        except (AttributeError, ValueError, KeyError):
            return None
