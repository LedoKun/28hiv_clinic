import numpy as np
import pandas as pd

from api import db
from api.models import InvestigationModel


class IxStats:
    df_raw = None

    def __init__(self):
        sql_statement = InvestigationModel.query.order_by(InvestigationModel.date.asc()).statement

        self.df_raw = pd.io.sql.read_sql(
            sql=sql_statement, con=db.session.bind
        )

        self.df_raw["date"] = pd.to_datetime(
            self.df_raw["date"], errors="coerce"
        )

        self.df_raw.set_index("date")

    def getCD4(self, isInit=False):
        try:
            result = {}
            df_data = self.df_raw[["date", "patient_id", "cd4"]]

            if isInit:
                df_data.sort_values("date", ascending=True, inplace=True)
                result["header"] = "Initial CD4 Levels"

            else:
                result["header"] = "Overall CD4 Levels"

            df_data = df_data.drop_duplicates(
                subset=["patient_id"], keep="first"
            )

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
