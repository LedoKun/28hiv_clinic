from api import db
from api.models import VisitModel
import pandas as pd
from collections import Counter


class VisitStats:
    df_raw = None
    df_cleaned = None
    df_last = None

    def __init__(self):
        self.df_raw = pd.io.sql.read_sql(
            sql=VisitModel.query.statement, con=db.session.bind
        )

        self.df_raw["date"] = pd.to_datetime(
            self.df_raw["date"], errors="coerce"
        )

        self.df_raw.set_index("date")

        # ARV
        self.df_raw["arv"] = self.df_raw["arv"].apply(VisitStats.listToStr)

        # antiTB
        self.df_raw["antiTB"] = self.df_raw["antiTB"].apply(
            VisitStats.listToStr
        )

        self.df_raw.sort_values("date", ascending=True, inplace=True)
        self.df_cleaned = self.df_raw.fillna(value="N/A")

        try:
            # keep only last visit per patient
            self.df_last = self.df_cleaned.drop_duplicates(
                subset=["patient_id"], keep="last"
            )

        except KeyError:
            self.df_last = None

    @staticmethod
    def listToStr(input_list):
        if input_list and isinstance(input_list, list):
            input_list.sort()

            return ", ".join(input_list)

        else:
            return None

    def getNewPatientsByMonth(self):
        try:
            new_patient = self.df_cleaned.sort_values(
                "date", ascending=True
            ).drop_duplicates(subset=["patient_id"])

            new_patient = (
                new_patient.groupby(new_patient["date"].dt.strftime("%m/%Y"))
                .count()
                .unstack()
            )["patient_id"]

            # rename columns
            df_new_patient_by_months = new_patient.to_frame(name="จำนวน")
            df_new_patient_by_months.index.names = ["เดือน"]

            return df_new_patient_by_months

        except (AttributeError, ValueError, KeyError):
            return None

    def getVisitsByMonth(self):
        try:
            all_visits_by_months = (
                self.df_cleaned.groupby(
                    self.df_cleaned["date"].dt.strftime("%m/%Y")
                )
                .count()
                .unstack()
            )["patient_id"]

            # rename columns
            df_all_visits_by_months = all_visits_by_months.to_frame(
                name="จำนวน"
            )
            df_all_visits_by_months.index.names = ["เดือน"]

            return df_all_visits_by_months

        except (AttributeError, ValueError, KeyError):
            return None

    def getCount(self, fieldName=[], name="รายการ"):
        try:
            series_count = self.df_last.groupby(fieldName).size()

            # rename columns
            df_count = series_count.to_frame(name="จำนวน")
            df_count.index.names = [name]

            return df_count

        except (AttributeError, ValueError, KeyError):
            return None

    @staticmethod
    def count_in_list(data_list):
        if not isinstance(data_list, list) or not data_list:
            return None

        else:
            flat_list = [
                item
                for sublist in data_list
                for sub2list in sublist
                for item in sub2list
            ]

            return Counter(flat_list)

    def getCountEach(self, dfField=[], name="Breakdown", isAll=True):
        if isAll:
            count_unique = VisitStats.count_in_list(
                self.df_cleaned[dfField].values.tolist()
            )

        else:
            count_unique = VisitStats.count_in_list(
                self.df_last[dfField].values.tolist()
            )

        count_df = pd.DataFrame(
            list(count_unique.items()), columns=[name, "Count"]
        )
        count_df.set_index(name, inplace=True)

        return count_df

    # TODO
    def getLengthUntilFirstARV(self):
        pass
