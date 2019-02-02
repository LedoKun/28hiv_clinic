import re

from fuzzywuzzy import fuzz


def type_hn(input):
    matched = re.match(r"(\d+/\d+-\d+)", input)

    if matched:
        return matched[0]

    else:
        return None


def type_date(input):
    matched = re.match(r"(\d{2}/\d{2}/\d{4})", input)

    if matched:
        return matched[0]

    else:
        return None


def type_int(input):
    matched = re.match(r"(\d+)", input)

    if matched:
        return matched[0]

    else:
        return None


def type_float(input):
    matched = re.match(r"(\d+\.\d+)", input)

    if matched:
        return matched[0]

    else:
        return None


def type_posneg(input):
    ratio = fuzz.partial_ratio("Positive", input)

    if ratio > 75:
        return "+ ve"

    else:
        return "- ve"


def type_reactive(input):
    ratio = fuzz.partial_ratio("Reactive", input)

    if ratio > 75:
        return "+ ve"

    else:
        return "- ve"


def type_vl(input):
    isMatched = re.search(r"<\s*\d{2}", input)

    if isMatched:
        return 0

    else:
        vl = re.match(r"(\d)", input)

        return vl[0]


def type_rpr(input):
    matched = re.search(r"1:(\d{2})", input)

    if matched:
        return matched[0]

    else:
        return None


labs_schema = {
    {"name": "HN", "field_name": "", "type": type_hn},
    {"name": "Order date.", "field_name": "date", "type": type_date},
    {"name": "Glucose(FBS)", "field_name": "fbs", "type": type_int},
    {"name": "Cholesterol", "field_name": "chol", "type": type_int},
    {"name": "Triglyceride", "field_name": "tg", "type": type_int},
    {"name": "BUN", "field_name": "bun", "type": type_int},
    {"name": "Creatinine", "field_name": "cr", "type": type_float},
    {"name": "Sodium(Na+)", "field_name": "na", "type": type_int},
    {"name": "Potassium(K+)", "field_name": "k", "type": type_float},
    {"name": "Chloride(Cl-)", "field_name": "cl", "type": type_int},
    {"name": "Bicarbonate(HCO3-)", "field_name": "hco3", "type": type_int},
    {"name": "Phosphorus(P)", "field_name": "po4", "type": type_float},
    {"name": "HIV-1RNA Viral load", "field_name": "vl", "type": "str"},
    {"name": "%CD4", "field_name": "pCD4", "type": type_float},
    {"name": "CD4", "field_name": "cd4", "type": type_int},
    {"name": "Hb", "field_name": "hb", "type": type_float},
    {"name": "Hct", "field_name": "hct", "type": type_float},
    {"name": "WBC", "field_name": "wbc", "type": type_float},
    {"name": "Neutrophils", "field_name": "wbcPNeu", "type": type_float},
    {"name": "Eosinophils", "field_name": "wbcPEos", "type": type_float},
    {"name": "Basophils", "field_name": "wbcPBasos", "type": type_float},
    {"name": "Lymphocytes", "field_name": "wbcPLym", "type": type_float},
    {"name": "Monocytes", "field_name": "wbcPMono", "type": type_float},
    {"name": "Anti-HIV", "field_name": "antiHIV", "type": type_posneg},
    {"name": "HBs-Ag", "field_name": "hbsag", "type": type_posneg},
    {"name": "Anti-HBs", "field_name": "antiHBs", "type": type_posneg},
    {"name": "Anti-HCV", "field_name": "antiHCV", "type": type_posneg},
    {"name": "Syphilis AB(RPR)", "field_name": "vdrl", "type": type_reactive},
    {"name": "RPR titer", "field_name": "rpr", "type": type_rpr},
}
