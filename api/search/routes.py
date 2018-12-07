from api.search import bp_api
from api.search.icd10_search import icd10Search
from api.search.patient_search import patientSearch

bp_api.add_resource(icd10Search, "/icd10")
bp_api.add_resource(patientSearch, "/patient")
