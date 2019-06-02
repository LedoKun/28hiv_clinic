import json
import re

import click
from flask import current_app

from hivclinic import db
from hivclinic.models.investigation_model import InvestigationModel
from hivclinic.models.visit_model import VisitModel
from hivclinic.models.patient_model import PatientModel
from hivclinic.schemas.investigation_schema import InvestigationSchema
from hivclinic.schemas.patient_schema import PatientSchema
from hivclinic.schemas.visit_schema import VisitSchema


ARV_MED_REGEX = [
    ["Teevir", r"TEEVIR"],
    ["TENO-EM", r"(?<!\(PEP\))TENO-EM"],
    ["Efavirenz (600)", r"Efavirenz.600"],
    ["Efavirenz (200/400mg)", r"Efavirenz.200"],
    ["Tenofovir", r"TENOFOVIR"],
    ["Lamivudine", r"Lamivudine"],
    ["Abacavir", r"Abacavir"],
    ["Raltegravir", r"Raltegravir"],
    ["Zidovudine", r"Zidovudine|zidovudine"],
    ["Zilarvir [AZT(300)/3TC(150)]", r"ZILARVIR|Zilavir"],
    ["Combivir [AZT(300)/3TC(150)]", r"Combivir"],
    ["Nevirapine", r"Nevirapine"],
    ["Lopinavir", r"Lopinavir"],
    ["GPO-VIR Z250", r"GPO-VIR.Z250"],
    ["GPO-VIR S30", r"GPO-VIR.S30"],
    ["Rilpivirine", r"(?<!\(PEP\))Rilpivirine"],
    ["TDF300+FTC200", r"(?<!PrEP)\(TDF300\+FTC200\)"],
    ["TDF300+3TC300+EFV600", r"TDF300\+3TC300\+EFV600"],
    ["Lamivir", r"LAMIVIR"],
]

OI_MED_REGEX = [
    ["Azithromycin", r"Azithromycin"],
    ["Fluconazole", r"Fluconazole"],
    ["Bactrim", r"Co-Trimoxazole"],
]

TB_MED_REGEX = [
    ["Rifampicin", r"Rifampicin"],
    ["Ethambutol", r"Ethambutol"],
    ["Isoniazid", r"(?:Isoniazid|i\.n\.h)"],
    ["Pyrazinamide", r"Pyrazinamide"],
    ["Kanamycin", r"Kanamycin"],
    ["Gentamicin", r"Gentamicin"],
    ["Ethionamide", r"Ethionamide"],
    ["Cycloserine", r"Cycloserine"],
    ["Levofloxacin", r"Levofloxacin"],
]


def register(app):
    @app.cli.group()
    def patient():
        """Patient related commands."""
        pass

    @patient.command()
    def drop():
        """Drop patient database"""
        if not current_app.config["PRODUCTION"]:
            current_app.logger.warn(
                "{} table dropped.".format(PatientModel.__table__)
            )
            PatientModel.__table__.drop(db.engine)

        else:
            current_app.logger.error(
                "This function only works in developent/testing mode only."
            )

    def convertToDate(date_str: str):
        date_str = date_str.split(" ")[0]

        thai_date_regex = r"(\d+)\/(\d+)\/(\d+)"
        match = re.search(thai_date_regex, date_str)

        if match:
            day, month, year = match.groups()
            year = int(year)

            if year > 2500:
                year = year - 543

            date_str = f"{year}-{month}-{day}"

        return date_str

    def patch_patient(patient_data):
        patient_data["dateOfBirth"] = convertToDate(
            patient_data["dateOfBirth"]
        )

        patient_schema = PatientSchema(many=False, unknown="EXCLUDE")

        patient = PatientModel.query.filter(
            PatientModel.hn == patient_data["hn"]
        ).first()

        try:
            if patient:
                patient_data["id"] = patient.id
                new_patient_model = patient_schema.load(
                    patient_data, transient=True
                )
                new_patient_dict = patient_schema.dump(new_patient_model)
                patient.update(**new_patient_dict)

            else:
                patient = patient_schema.load(patient_data)

            patient.imported = True

            return patient

        except Exception as e:
            current_app.logger.warn(
                f"Unable to import patient HN {patient_data['hn']}"
                f" with this error {e}, skipping."
            )

            raise e

    @patient.command()
    @click.argument("json_path")
    def importjson(json_path):
        """Import patient from json file"""
        with open(json_path, "r") as file:
            patients = json.load(file)

        for patient in patients:
            dermographic = patient.pop("dermographic")
            ixs = patient.pop("ix")
            visits_hcis = patient.pop("visits")
            medications_hcis = patient.pop("med")

            # add patient
            patient_model = patch_patient(dermographic)
            db.session.add(patient_model)
            db.session.commit()

            # add ix
            ix_schema = InvestigationSchema(many=False)

            for ix in ixs:
                ix["date"] = convertToDate(ix["date"])

                # find previous data
                ix_model = (
                    InvestigationModel.query.filter(
                        InvestigationModel.imported == True  # noqa
                    )
                    .filter(InvestigationModel.patientID == patient_model.id)
                    .filter(InvestigationModel.date == ix["date"])
                    .first()
                )

                try:
                    new_ix_model = ix_schema.load(ix)

                    if ix_model:
                        new_ix_dict = ix_schema.dump(new_ix_model)
                        ix_model.update(**new_ix_dict)

                    else:
                        ix_model = new_ix_model
                        ix_model.patientID = patient_model.id
                        ix_model.imported = True

                except Exception as e:
                    current_app.logger.warn(
                        f"Unable to import investigation of "
                        f"patient HN {patient_model.hn} "
                        f"on {ix['date']}"
                        f" with this error {e}, skipping."
                    )
                    continue

                # set imported status

                db.session.add(ix_model)

            # add visits
            visit_schema = VisitSchema(many=False)

            for item in medications_hcis:
                date = item[0]
                arvMedications = []
                tbMedications = []
                oiMedications = []
                medications = item[1]
                impression = []

                # if medications were prescribed
                if item[1]:
                    all_medication_string = "::".join(item[1]).lower()

                    for regex_item in ARV_MED_REGEX:
                        if re.search(
                            regex_item[1], all_medication_string, re.IGNORECASE
                        ):
                            arvMedications.append(regex_item[0])

                    for regex_item in TB_MED_REGEX:
                        if re.search(
                            regex_item[1], all_medication_string, re.IGNORECASE
                        ):
                            tbMedications.append(regex_item[0])

                    # add diagnosis
                    arv_string = "::".join(arvMedications).lower() or ""
                    tb_string = "::".join(tbMedications).lower() or ""

                    if (
                        ("teevir" in arv_string)
                        or ("gpo-vir" in arv_string)
                        or ("TDF300+3TC300+EFV600".lower() in arv_string)
                        or (len(arvMedications) >= 3)
                        or (
                            len(arvMedications) >= 2
                            and (
                                ("teno-em" in arv_string)
                                or ("zilarvir" in arv_string)
                                or ("combivir" in arv_string)
                            )
                        )
                    ):
                        impression.append(
                            "B20: Human immunodeficiency virus [HIV] disease"
                        )

                    if "isoniazid" in tb_string and len(tbMedications) == 1:
                        impression.append(
                            "R7611: Nonspecific reaction to tuberculin skin "
                            + "test without active tuberculosis"
                        )

                    if len(tbMedications) >= 2:
                        impression.append(
                            "A159: Respiratory tuberculosis unspecified"
                        )

                # oi medications, must have HIV first
                if "HIV".lower() in "::".join(impression).lower():
                    for regex_item in OI_MED_REGEX:
                        if re.search(
                            regex_item[1], all_medication_string, re.IGNORECASE
                        ):
                            oiMedications.append(regex_item[0])

                # add other STD dx
                if "Benzathine Penicillin".lower() in all_medication_string:
                    impression.append("A539: Syphilis, unspecified")

                visit_entry = {
                    "date": convertToDate(date),
                    "arvMedications": sorted(arvMedications),
                    "tbMedications": sorted(tbMedications),
                    "oiMedications": sorted(oiMedications),
                    "medications": sorted(medications),
                    "impression": sorted(impression),
                }

                # find previous data
                visit_model = (
                    VisitModel.query.filter(
                        VisitModel.imported == True  # noqa
                    )
                    .filter(VisitModel.patientID == patient_model.id)
                    .filter(VisitModel.date == visit_entry["date"])
                    .first()
                )

                try:
                    new_visit_model = visit_schema.load(visit_entry)

                    if visit_model:
                        new_visit_dict = visit_schema.dump(new_visit_model)
                        visit_model.update(**new_visit_dict)

                    else:
                        visit_model = new_visit_model
                        visit_model.patientID = patient_model.id
                        visit_model.imported = True

                except Exception as e:
                    current_app.logger.warn(
                        f"Unable to import visit of "
                        f"patient HN {patient_model.hn} "
                        f"on {ix['date']}"
                        f" with this error {e}, skipping."
                    )
                    continue

                db.session.add(visit_model)

                # remove duplicate entries visits
                try:
                    visits_hcis.remove(date)

                except ValueError:
                    pass

            for visit in visits_hcis:
                visit_entry = {"date": convertToDate(visit)}

                # find previous data
                visit_model = (
                    VisitModel.query.filter(
                        VisitModel.imported == True  # noqa
                    )
                    .filter(VisitModel.patientID == patient_model.id)
                    .filter(VisitModel.date == visit_entry["date"])
                    .first()
                )

                try:
                    new_visit_model = visit_schema.load(visit_entry)

                    if visit_model:
                        new_visit_dict = visit_schema.dump(new_visit_model)
                        visit_model.update(**new_visit_dict)

                    else:
                        visit_model = new_visit_model
                        visit_model.patientID = patient_model.id
                        visit_model.imported = True

                except Exception as e:
                    current_app.logger.warn(
                        f"Unable to import visit of "
                        f"patient HN {patient_model.hn} "
                        f"on {visit_entry['date']}"
                        f" with this error {e}, skipping."
                    )
                    continue

                db.session.add(visit_model)

            db.session.commit()
