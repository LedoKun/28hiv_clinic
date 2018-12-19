from datetime import date

from flask import jsonify
from flask_restful import Resource

import numpy as np
import pandas as pd
from api import db
from api.models import InvestigationModel, PatientModel, VisitModel
from flask_jwt_extended import jwt_required


class AllData:
    df_patients = None
    df_visits = None
    df_ix = None

    def __init__(self):
        # Patients information
        self.df_patients = pd.io.sql.read_sql(
            sql=PatientModel.query.with_entities(
                PatientModel.id,
                PatientModel.dob,
                PatientModel.sex,
                PatientModel.gender,
                PatientModel.payer,
                PatientModel.nationality,
                PatientModel.isRefer,
                PatientModel.referFrom,
                PatientModel.education,
            ).statement,
            con=db.session.bind,
        )

        # calculate age
        self.df_patients["age"] = self.df_patients["dob"].apply(
            AllData.calculate_age
        )

        self.df_patients.fillna(value="N/A", inplace=True)

        # Visits information
        self.df_visits = pd.io.sql.read_sql(
            sql=VisitModel.query.with_entities(
                VisitModel.id,
                VisitModel.date,
                VisitModel.bw,
                VisitModel.contactTB,
                VisitModel.adherenceScale,
                VisitModel.arv,
                VisitModel.oiProphylaxis,
                VisitModel.antiTB,
                VisitModel.vaccination,
                VisitModel.patient_id,
            ).statement,
            con=db.session.bind,
        )
        self.df_visits["date"] = pd.to_datetime(
            self.df_visits["date"], errors="coerce"
        )
        self.df_visits.set_index("date")

        self.df_visits.fillna(value="N/A", inplace=True)

        # Investigation information
        self.df_ix = pd.io.sql.read_sql(
            sql=InvestigationModel.query.with_entities(
                InvestigationModel.id,
                InvestigationModel.date,
                InvestigationModel.antiHIV,
                InvestigationModel.cd4,
                InvestigationModel.pCD4,
                InvestigationModel.vl,
                InvestigationModel.vdrl,
                InvestigationModel.rpr,
                InvestigationModel.hbsag,
                InvestigationModel.antiHBs,
                InvestigationModel.antiHCV,
                InvestigationModel.ppd,
                InvestigationModel.cxr,
                InvestigationModel.tb,
                InvestigationModel.patient_id,
            ).statement,
            con=db.session.bind,
        )
        self.df_ix["date"] = pd.to_datetime(
            self.df_ix["date"], errors="coerce"
        )
        self.df_ix.set_index("date")

        self.df_ix.fillna(value="N/A", inplace=True)

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


class Stats(Resource):
    @jwt_required
    def get(Resource):
        all_data = AllData()

        if all_data.df_patients.empty:
            return jsonify({})

        #########################
        # demographic data
        #########################
        # age
        bins = np.arange(0, 110, 10)

        df_groupby_age = (
            all_data.df_patients.groupby(
                ["sex", "gender", pd.cut(all_data.df_patients.age, bins)]
            )
            .size()
            .unstack()
        )

        # thais
        df_thais = all_data.df_patients.loc[
            all_data.df_patients["nationality"].isin(["Thailand"])
        ]
        df_thais_groupby_age = (
            df_thais.groupby(["sex", "gender", pd.cut(df_thais.age, bins)])
            .size()
            .unstack()
        )
        df_thais_groupby_payer = df_thais.groupby(["payer"]).size()

        # not thais
        df_non_thai = all_data.df_patients.loc[
            all_data.df_patients["nationality"] != "Thailand"
        ]
        df_non_thai_groupby_age = (
            df_non_thai.groupby(
                ["sex", "gender", pd.cut(df_non_thai.age, bins)]
            )
            .size()
            .unstack()
        )
        df_non_thai_groupby_payer = df_non_thai.groupby(["payer"]).size()

        # referral status
        df_isRefer = (
            all_data.df_patients.groupby(
                ["sex", "gender", "isRefer", "referFrom"]
            )
            .size()
            .unstack()
        )

        #########################
        # Visits
        #########################
        # new patients by months
        df_new_patient = all_data.df_visits.sort_values(
            "date", ascending=True
        ).drop_duplicates(subset=["patient_id"])
        df_new_patient_by_months = (
            df_new_patient.groupby(
                df_new_patient["date"].dt.strftime("%m/%Y")
            )
            .count()
            .unstack()
        )["patient_id"]

        # visits by months
        df_all_visits_by_months = (
            all_data.df_visits.groupby(
                all_data.df_visits["date"].dt.strftime("%m/%Y")
            )
            .count()
            .unstack()
        )["patient_id"]

        return jsonify(
            {
                "df_groupby_age": df_groupby_age,
                "df_thais_groupby_age": df_thais_groupby_age,
                "df_non_thai_groupby_age": df_non_thai_groupby_age,
                "df_thais_groupby_payer": df_thais_groupby_payer,
                "df_isRefer": df_isRefer,
                "df_non_thai_groupby_payer": df_non_thai_groupby_payer,
                "df_new_patient_by_months": df_new_patient_by_months,
                "df_all_visits_by_months": df_all_visits_by_months,
            }
        )
