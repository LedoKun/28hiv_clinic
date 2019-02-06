from collections import Counter
from datetime import timedelta

import pandas as pd
from sqlalchemy.orm import joinedload

from api import db
from api.models import PatientModel, VisitModel


class VisitStats:
    df_raw = None
    df_cleaned = None
    df_last = None
    df_days_until_arv = None

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

    def days_to_start_arv_df(self, df_data):
        if df_data is None or df_data.empty:
            return None

        # drop all rows that have none & drop uneeded columns
        df_data = df_data.dropna(how="any")

        bins = [
            pd.Timedelta(weeks=-1),
            pd.Timedelta(weeks=1),
            pd.Timedelta(weeks=2),
            pd.Timedelta(weeks=3),
            pd.Timedelta(weeks=4),
            pd.Timedelta(weeks=100),
        ]

        labels = [
            "0-7 Days",
            "8-14 Days",
            "15-21 Days",
            "22-28 Days",
            "29+ Days",
        ]

        df_data["bins"] = pd.cut(df_data["time_to_start"], bins, labels=labels)
        df_binned_timedelta = df_data.groupby(df_data["bins"]).count()

        # rename columns
        df_binned_timedelta.columns = ["จำนวน"]
        df_binned_timedelta.index.names = ["ช่วงเวลา"]

        # other stats
        arv_start_stats = pd.DataFrame(df_data.describe())
        arv_start_stats.columns = ["ข้อมูล"]

        return {"df_data": df_binned_timedelta, "df_describe": arv_start_stats}

    def getDaysToStartARV(self):
        df_data = self.countDaysToStartARV()
        min_year = int(df_data.year.min().item())
        max_year = int(df_data.year.max().item())

        results = []

        # bin each year data
        for year in range(min_year, max_year + 1):
            try:
                df_year = df_data[df_data.year == year]

                result = self.days_to_start_arv_df(
                    df_data=df_year[["time_to_start"]]
                )
                result["header"] = str(year) + " - Number of Days To Start ARV"
                results.append(result)

            except (AttributeError, ValueError, KeyError):
                continue

        # bin overall data
        try:
            overall = self.days_to_start_arv_df(
                df_data=df_data[["time_to_start"]]
            )
            overall["header"] = "Overall" + " - Days To Start ARV"
            results.append(overall)

        except (AttributeError, ValueError, KeyError):
            pass

        return results

    def countDaysToStartARV(self):
        if self.df_days_until_arv and not self.df_days_until_arv.empty:
            return self.df_days_until_arv

        # get visit for patients that haven't
        # started ARV but was Dx with B20
        query = (
            db.session.query(VisitModel)
            .options(joinedload("patient", innerjoin=True))
            .filter(
                PatientModel.patientStatus != "ผู้ป่วยรับโอน (เริ่ม ARV แล้ว)"
            )
            .filter(
                VisitModel.impression.any(
                    "B20 - Human immunodeficiency virus [HIV] disease"
                )
            )
            .order_by(VisitModel.date.asc())
            .with_entities(
                VisitModel.date, VisitModel.patient_id, VisitModel.arv
            )
        )

        df_days_until_arv = pd.io.sql.read_sql(
            sql=query.statement, con=db.session.bind
        )

        # calculate time_delta
        time_delta = []
        all_patient_ids = df_days_until_arv.patient_id.unique()

        for id in all_patient_ids:
            df_patient_visits = df_days_until_arv.loc[
                df_days_until_arv["patient_id"] == id
            ]

            first_visit = None
            start_arv = None

            for id, row in df_patient_visits.iterrows():
                if row["arv"] and not first_visit:
                    time_delta.append(
                        {
                            "patient_id": id,
                            "time_to_start": timedelta(0),
                            "year": row["date"].year,
                        }
                    )

                    break

                elif not row["arv"] and not first_visit:
                    first_visit = row["date"]

                elif row["arv"] and first_visit and not start_arv:
                    start_arv = row["date"]
                    delta = start_arv - first_visit

                    if delta > timedelta(0):
                        time_delta.append(
                            {
                                "patient_id": id,
                                "time_to_start": delta,
                                "year": first_visit.year,
                            }
                        )

                    else:
                        time_delta.append(
                            {
                                "patient_id": id,
                                "time_to_start": timedelta(0),
                                "year": first_visit.year,
                            }
                        )

                    break

        results_df = pd.DataFrame(time_delta)
        results_df["year"] = pd.to_numeric(results_df["year"])

        # save the df for later use
        self.df_days_until_arv = results_df
        return results_df
