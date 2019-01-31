from flask import jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from api.utils.stats.patients import PatientStats
from api.utils.stats.visits import VisitStats
from api.utils.stats.investigation import IxStats


class Stats(Resource):
    @jwt_required
    def get(Resource):
        patients = PatientStats()
        visits = VisitStats()
        ix = IxStats()

        return jsonify(
            {
                "df_groupby_age": patients.getAgeSexGenderDF(),
                "df_thais_groupby_age": patients.getAgeSexGenderDF(
                    include=["Thailand"]
                ),
                "df_non_thai_groupby_age": patients.getAgeSexGenderDF(
                    exclude=["Thailand"]
                ),
                "df_thais_groupby_payer": patients.getPayerDF(
                    include=["Thailand"]
                ),
                "df_non_thai_groupby_payer": patients.getPayerDF(
                    exclude=["Thailand"]
                ),
                "df_count_patient_status": patients.getCount(
                    fieldName=["nationality", "patientStatus"],
                    name=["Nationality"],
                ),
                "df_isRefer": patients.getRefferalDF(),
                "df_new_patient_by_months": visits.getNewPatientsByMonth(),
                "df_all_visits_by_months": visits.getVisitsByMonth(),
                "df_arv": visits.getCount(fieldName=["arv"], name="Regimens"),
                "days_start_arv_yearly": visits.getDaysToStartARV(),
                "df_antiTB": visits.getCount(
                    fieldName=["antiTB"], name="Regimens"
                ),
                "df_impression": visits.getCountEach(
                    dfField=["impression"], name="Impression", isAll=False
                ),
                "df_oiProphylaxis": visits.getCountEach(
                    dfField=["oiProphylaxis"], name="OI Medication"
                ),
                "df_vaccination": visits.getCountEach(
                    dfField=["vaccination"], name="Vaccine"
                ),
                "init_cd4": ix.getCD4(isInit=True),
                "cd4": ix.getCD4(isInit=False),
            }
        )
