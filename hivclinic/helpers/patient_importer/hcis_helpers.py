import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

EXPLICIT_WAIT = 10

LABS_REGEX = [
    ["viralLoad", r"(?:VL|Viral.*):::(<\s*\d+|\d+)"],
    ["percentCD4", r"(?:%CD4):::(\d+.\d+|\d+)"],
    ["absoluteCD4", r"(?:(?<!%)CD4):::(\d+.\d+|\d+)"],
    ["hemoglobin", r"(?:Hb):::(\d+.\d+|\d+)"],
    ["hematocrit", r"(?:Hct):::(\d+.\d+|\d+)"],
    ["whiteBloodCellCount", r"(?:WBC):::(\d+.\d+|\d+)"],
    ["neutrophilsPct", r"(?:Neutrophils):::(\d+.\d+|\d+)"],
    ["eosinophilsPct", r"(?:Eosinophils):::(\d+.\d+|\d+)"],
    ["basophilsPct", r"(?:Basophils):::(\d+.\d+|\d+)"],
    ["lymphocytesPct", r"(?:Lymphocytes):::(\d+.\d+|\d+)"],
    ["monocytesPct", r"(?:Monocytes):::(\d+.\d+|\d+)"],
    ["fbs", r"(?:Glucose.+):::(\d+.\d+|\d+)"],
    ["hemoglobinA1c", r"(?:HbA1C.+):::(\d+.\d+|\d+)"],
    ["cholesterol", r"(?:Cholesterol):::(\d+.\d+|\d+)"],
    ["triglycerides", r"(?:Triglyceride):::(\d+.\d+|\d+)"],
    ["creatinine", r"(?:Creatinine):::(\d+.\d+|\d+)"],
    ["ast", r"(?:AST):::(\d+.\d+|\d+)"],
    ["alt", r"(?:ALT):::(\d+.\d+|\d+)"],
    ["alp", r"(?:ALP):::(\d+.\d+|\d+)"],
    ["sodium", r"(?:Sodium.+):::(\d+.\d+|\d+)"],
    ["potassium", r"(?:Potassium.+):::(\d+.\d+|\d+)"],
    ["chloride", r"(?:Chloride.+):::(\d+.\d+|\d+)"],
    ["bicarbonate", r"(?:Bicarbonate.+):::(\d+.\d+|\d+)"],
    ["phosphate", r"(?:Phosphate.+):::(\d+.\d+|\d+)"],
    ["antiHIV", r"(?:Anti-HIV.+):::(\w+)"],
    ["HBsAg", r"(?:HBs-Ag.+):::(\w+)"],
    ["antiHBs", r"(?:Anti-HBs.+):::(Negative|Positive)"],
    ["antiHCV", r"(?:Anti-HCV):::(\w+)"],
    ["tpha", r"(?:TPHA.+):::(\w+)"],
    ["rpr", r"(?:Syphilis Ab\(RPR\).+):::1:(\d+)"],
    ["cryptoAg", r"(?:Cryptococcus.+):::(\w+)"],
    ["afb", r"(?:AFB stain.+):::(Negative|Scanty|\d+\+)"],
    ["geneXpert", r"(?:GeneXpert.+):::([\w\ ]+)"],
    ["tbCulture", r"(?:TB Culture.+):::([\w\ ]+)"],
    ["dst", r"(?:DST-TB.+):::([\w:,\ ]+)"],
    ["lpa", r"(?:LPA.+):::([\w:,\ ]+)"],
]


def waitForLoad(
    driver, timeout_sec: int = EXPLICIT_WAIT, wait_for_dom: bool = False
):
    if wait_for_dom:
        WebDriverWait(driver, timeout_sec).until(
            lambda d: (
                driver.execute_script("return document.readyState")
                == "complete"
            )
        )

    try:
        WebDriverWait(driver, timeout_sec).until(
            EC.invisibility_of_element_located((By.ID, "AWMID"))
        )

    except Exception:
        pass


def convertToDate(date_str: str):
    # convert to AD
    date_str = date_str.split("/")

    if int(date_str[2]) > 2500:
        date_str[2] = int(date_str[2]) - 543

    return f"{date_str[0]}/{date_str[1]}/{date_str[2]}"


def searchHN(driver, text_box_id: str, hn: str):
    """Enter and search HN for right upper text input"""
    # search for the HN

    search_box = WebDriverWait(driver, EXPLICIT_WAIT).until(
        EC.element_to_be_clickable((By.ID, text_box_id))
    )
    search_box.send_keys(Keys.CONTROL, "a", Keys.ENTER)
    search_box.send_keys(hn)
    search_box.send_keys(Keys.TAB)


def isNextPageLinkExists(driver):
    next_page_link_css = "td > a[href*='PageNext']"

    soup = BeautifulSoup(driver.page_source, "lxml")
    is_next_page_link = bool(soup.select_one(next_page_link_css))

    if is_next_page_link:
        return WebDriverWait(driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_link_css))
        )

    else:
        return False


def clickNew(driver):
    new_button_xpath = (
        '//img[contains(@src, "new_disa_32x32.gif") '
        'or contains(@src, "new_enab_32x32.gif")]'
    )

    new_patient = WebDriverWait(driver, EXPLICIT_WAIT).until(
        EC.element_to_be_clickable((By.XPATH, new_button_xpath))
    )
    new_patient.click()


def setInputDate(driver, input_id: str, date_str: str):
    date_input = WebDriverWait(driver, EXPLICIT_WAIT).until(
        EC.element_to_be_clickable((By.ID, input_id))
    )

    # I don't know but this keys combination works
    date_input.send_keys(Keys.CONTROL, "a", Keys.ENTER)
    date_input.send_keys(date_str, Keys.ENTER)

    # wait for the form to update
    date_input = WebDriverWait(driver, EXPLICIT_WAIT).until(
        EC.text_to_be_present_in_element_value((By.ID, input_id), date_str)
    )


def praseVisits(page_source):
    soup = BeautifulSoup(page_source, "lxml")

    visit_dates = soup.select(
        "span[id*='objdw_cnifcn_grd_ovst_detail_0'] >"
        + " input[name*='compute_1_']"
    )
    visit_dates = [
        convertToDate(element.get("value").split(" ")[0])
        for element in visit_dates
    ]

    return visit_dates


def praseTwoTablePage(
    driver,
    date_element_xpath: str,
    element_text_split_by: str,
    elementsPraser: object,
) -> list:
    results = []

    # wait
    waitForLoad(driver)

    elements = driver.find_elements_by_xpath(date_element_xpath)

    for element in elements:
        date_str = element.text.split(element_text_split_by)[0]
        date_str = convertToDate(date_str)

        # scrolls items into view
        driver.execute_script("return arguments[0].scrollIntoView();", element)

        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        actions.double_click(element).perform()

        # wait
        waitForLoad(driver)

        # get list of subelements
        subelement_result = elementsPraser(page_source=driver.page_source)
        results.append([date_str, subelement_result])

    return results


def praseMedication(page_source) -> list:
    read_from_name_regex = r"^meditem_name_\d+"

    soup = BeautifulSoup(page_source, "lxml")
    medications = soup.find_all(
        "span", attrs={"name": re.compile(read_from_name_regex)}
    )

    return [med.text for med in medications]


def praseInvestigation(page_source) -> str:
    lab_string = ""

    ix_name_regex = r"^labexm_labexmnm_\d+"
    ix_result_regex = r"^compute_2_\d+"

    soup = BeautifulSoup(page_source, "lxml")
    lab_names = soup.find_all(
        "input", attrs={"name": re.compile(ix_name_regex)}
    )
    lab_results = soup.find_all(
        "input", attrs={"name": re.compile(ix_result_regex)}
    )

    lab_names = [name.get("value") for name in lab_names]
    lab_results = [result.get("value") for result in lab_results]

    labs = list(zip(lab_names, lab_results))

    for lab in labs:
        if not lab_string:
            lab_string = "{}:::{}\n".format(lab[0], lab[1])

        else:
            lab_string = lab_string + "{}:::{}\n".format(lab[0], lab[1])

    return lab_string


def praseHN(page_source):
    soup = BeautifulSoup(page_source, "lxml")
    HNs = soup.find_all("span", attrs={"name": re.compile(r"c_hn_\d+")})
    HNs = [element.text for element in HNs]

    return HNs


def matchLabs(allLabs: list):
    labs = []
    for rawLab in allLabs:
        lab = {}

        # convert to AD
        date = convertToDate(rawLab[0])
        lab["date"] = date

        for regex_str in LABS_REGEX:
            match = re.search(regex_str[1], rawLab[1])

            if match:
                lab[regex_str[0]] = match.group(1)

        labs.append(lab)

    return labs


def encodeStr(data):
    """HCIS's stupid username & password encoder"""
    finalString = ""
    tmp = ""

    if not data:
        return ""

    # get temporary data
    if len(data) > 2:
        tmp = data[1 : len(data) - 1]  # noqa

    data = data[len(data) - 1 : len(data)] + tmp + data[0:1]  # noqa

    for i in range(0, len(data)):
        if finalString == "":
            finalString = str(ord(data[i]))

        else:
            finalString += "@" + str(ord(data[i]))

    return finalString


def praseDermographic(page_source, hn):
    soup = BeautifulSoup(page_source, "lxml")

    firstname = soup.find("input", {"id": "objdw_ex_crd_0_13"}).get("value")
    lastname = soup.find("input", {"id": "objdw_ex_crd_0_14"}).get("value")

    dateOfBirth = (
        soup.find("input", {"id": "objdw_ex_crd_0_22"}).get("value") or None
    )
    dateOfBirth = convertToDate(dateOfBirth)

    sex = (
        soup.select_one(
            "input[name='objdw_ex_crd_pt_sex_0'][type='radio']:checked + span"
        ).text
        or None
    )
    maritalStatus = (
        soup.select_one("select[id='objdw_ex_crd_0_35'] > option:checked").text
        or None
    )
    nationality = (
        soup.select_one("select[id='objdw_ex_crd_0_27'] > option:checked").text
        or None
    )

    governmentID = (
        soup.find("input", {"id": "objdw_ex_crd_0_19"}).get("value") or None
    )

    healthInsurance = (
        soup.select_one(
            "select[id='objdw_pt_newcp_0_44'] > option:checked"
        ).text
        or None
    )

    return {
        "hn": hn,
        "name": f"{firstname} {lastname}",
        "dateOfBirth": dateOfBirth,
        "sex": sex,
        "maritalStatus": maritalStatus,
        "nationality": nationality,
        "governmentID": governmentID,
        "healthInsurance": healthInsurance,
    }


def praseDermographicTab2(page_source):
    soup = BeautifulSoup(page_source, "lxml")
    address = ""
    phoneNumbers = []

    # address
    st_number = (
        soup.find("input", {"id": "objdw_ex_addr_0_4"}).get("value") or ""
    )
    moo = soup.find("input", {"id": "objdw_ex_addr_0_5"}).get("value") or ""
    soi = soup.find("input", {"id": "objdw_ex_addr_0_6"}).get("value") or ""
    st = soup.find("input", {"id": "objdw_ex_addr_0_7"}).get("value") or ""
    province = (
        soup.find("input", {"id": "objdw_ex_addr_0_9"}).get("value") or ""
    )
    country = (
        soup.find("input", {"id": "objdw_ex_addr_0_16"}).get("value") or ""
    )
    zip_code = (
        soup.find("input", {"id": "objdw_ex_addr_0_13"}).get("value") or ""
    )

    address = (
        f"{'เลขที่/อาคาร '*bool(st_number)}{st_number}{' '*bool(st_number)}"
        f"{'หมู่ที่ '*bool(moo)}{moo}{' '*bool(moo)}"
        f"{'ตรอก/ซอย'*bool(soi)}{soi}{' '*bool(soi)}"
        f"{'ถนน'*bool(st)}{st}{' '*bool(st)}"
        f"{province}{' '*bool(province)}"
        f"{'ประเทศ'*bool(country)}{country}{' '*bool(country)}"
        f"{zip_code}"
    )

    # phones
    phone_base_id = "objdw_ex_addr_0_"

    for x in range(14, 16):
        phone = soup.find("input", {"id": phone_base_id + str(x)}).get("value")

        if phone:
            phoneNumbers.append(phone)

    return {"address": address, "phoneNumbers": phoneNumbers}


def isElementPresent(driver, by, value):
    try:
        driver.find_element(by=by, value=value)
    except NoSuchElementException:
        return False
    return True


def newWindow(driver):
    multi_window = driver.window_handles

    for window in multi_window:
        driver.switch_to.window(window)
        driver.close()

    # open a new window
    driver.execute_script("window.open('');")
