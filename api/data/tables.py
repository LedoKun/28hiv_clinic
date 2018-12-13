from flask import jsonify
from flask_restful import Resource

from api.models import PatientModel, VisitModel, InvestigationModel
from flask_jwt_extended import jwt_required

import pandas as pd
from api import db
from datetime import date
import numpy as np

import sys


class AllData:
    df_patients = None
    df_visits = None
    df_ix = None

    def __init__(self):
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

    @staticmethod
    def calculate_age(born):
        today = date.today()
        return (
            today.year
            - born.year
            - ((today.month, today.day) < (born.month, born.day))
        )


class Tables(Resource):
    # @jwt_required
    def get(Resource):
        all_data = AllData()

        #########################
        # demographic data
        #########################
        # age
        bins = np.arange(0, 100, 10)
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

        #########################
        # Visits
        #########################
        df_all_visits_by_months = (
            all_data.df_visits.groupby(
                all_data.df_visits["date"].dt.strftime("%m/%Y")
            )
            .count()
            .unstack()
        )["patient_id"]

        print(df_groupby_age, file=sys.stdout)
        print(df_thais_groupby_age, file=sys.stdout)
        print(df_thais_groupby_payer, file=sys.stdout)
        print(df_non_thai_groupby_age, file=sys.stdout)
        print(df_non_thai_groupby_payer, file=sys.stdout)
        print(df_all_visits_by_months, file=sys.stdout)

        return jsonify({"msg": "okay"})
