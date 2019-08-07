import re

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

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
    ["antiHBs", r"(?:Anti-HBs):::(\w+)"],
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


def waitForPageReady(wait):
    loading_css = "#AWMOD"
    wait.until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_css))
    )


def convertToDate(date_str: str):
    # convert to AD
    date_str = date_str.split("/")

    if int(date_str[2]) >= 2100:
        date_str[2] = int(date_str[2]) - 543

    return f"{date_str[0]}/{date_str[1]}/{date_str[2]}"


def readHN(page_source):
    hn_span_css = "span[name=t_hndsp_0]"
    soup = BeautifulSoup(page_source, "lxml")

    try:
        hn = soup.select_one(hn_span_css).text

    except Exception:
        hn = None

    return hn


def waitForHNToLoaded(wait, hn):
    wait.until(lambda d: (readHN(d.page_source) == hn))


def searchHN(wait, text_box_css: str, hn: str):
    """Enter and search HN for right upper text input"""
    # search for the HN
    search_box = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, text_box_css))
    )

    search_box.send_keys(Keys.CONTROL, "a", Keys.ENTER)
    search_box.send_keys(hn)
    search_box.send_keys(Keys.TAB)


def isNextPageLinkExists(driver, wait):
    next_page_link_css = "td > a[href*='PageNext']"

    soup = BeautifulSoup(driver.page_source, "lxml")
    is_next_page_link = bool(soup.select_one(next_page_link_css))

    if is_next_page_link:
        return wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, next_page_link_css)
            )
        )

    else:
        return False


def isDisplayPatientInfo(driver, wait):
    hn_css = "span[name='t_hndsp_0']"

    soup = BeautifulSoup(driver.page_source, "lxml")
    return bool(soup.select_one(hn_css))


def clickNew(wait, click_new_button=True):
    if click_new_button:
        new_button_css = (
            "img[src$='new_disa_32x32.gif'], " "img[src$='new_enab_32x32.gif']"
        )

    else:
        new_button_css = "img[src$='exit_enab_32x32.gif']"

    new_patient = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, new_button_css))
    )
    new_patient.click()


def setInputDate(wait, input_id: str, date_str: str):
    date_input = wait.until(EC.presence_of_element_located((By.ID, input_id)))

    # I don't know but this keys combination works
    date_input.send_keys(Keys.CONTROL, "a", Keys.ENTER)
    date_input.send_keys(date_str, Keys.ENTER)

    # wait for the form to update
    date_input = wait.until(
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

    primary_care = (
        soup.find("input", id="objdw_cnifcn_ext_ovst_0_28").get("value") or "-"
    )

    secondary_care = (
        soup.find("input", id="objdw_cnifcn_ext_ovst_0_27").get("value") or "-"
    )

    regular_care = (
        soup.find("input", id="objdw_cnifcn_ext_ovst_0_29").get("value") or "-"
    )

    cares = f"{primary_care}/{secondary_care}/{regular_care}"

    return cares, visit_dates


def praseTwoTablePage(
    driver,
    wait,
    date_element_css: str,
    element_text_split_by: str,
    elementsPraser: object,
) -> list:
    results = []
    is_first_element = True

    while True:
        elements = driver.find_elements_by_css_selector(date_element_css)

        for element in elements:
            # read subelements
            first_page_source = driver.page_source
            first_hcis_class, _ = elementsPraser(
                page_source=driver.page_source, wait=wait
            )

            # read dates
            date_str = element.text.split(element_text_split_by)[0]
            date_str = convertToDate(date_str)

            # scrolls items into view
            driver.execute_script(
                "return arguments[0].scrollIntoView();", element
            )

            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            actions.double_click(element).perform()

            # wait
            waitForPageReady(wait=wait)

            if not is_first_element:
                wait.until(
                    lambda d: first_page_source != d.page_source
                    and isTwoTableGridLoaded(
                        elementsPraser(page_source=d.page_source, wait=wait)[
                            0
                        ],
                        first_hcis_class,
                    )
                )

            else:
                is_first_element = False

            _, results_grid = elementsPraser(
                page_source=driver.page_source, wait=wait
            )
            results.append([date_str, results_grid])

        # if there is a next page
        next_page = isNextPageLinkExists(driver, wait)

        if next_page:
            is_first_element = True
            next_page.click()

        else:
            break

    return results


def isTwoTableGridLoaded(a_class: str, b_class: str) -> bool:
    if a_class is None and b_class is None:
        return True

    elif a_class != b_class:
        return True

    else:
        return False


def praseMedication(page_source, wait) -> list:
    read_from_name_regex = r"^meditem_name_\d+"
    read_from_name_css = "span[name^='meditem_name_']"

    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, read_from_name_css)
            )
        )

    except TimeoutException:
        # no elements found
        soup = BeautifulSoup(page_source, "lxml")
        medications = soup.find_all(
            "span", attrs={"name": re.compile(read_from_name_regex)}
        )

        if not medications:
            pass

    else:
        soup = BeautifulSoup(page_source, "lxml")
        medications = soup.find_all(
            "span", attrs={"name": re.compile(read_from_name_regex)}
        )

    # get unique class from first result
    if medications:
        hcis_class = medications[0]["class"]

    else:
        hcis_class = None

    # sort result for later comparision
    medications = [med.text for med in medications]
    medications.sort()

    return hcis_class, medications


def praseInvestigation(page_source, wait) -> str:
    lab_string = ""

    ix_name_regex = r"^labexm_labexmnm_\d+"
    ix_result_regex = r"^compute_2_\d+"

    ix_result_css = "input[name^='compute_2_']"

    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ix_result_css))
        )

    except TimeoutException:
        soup = BeautifulSoup(page_source, "lxml")
        lab_names = soup.find_all(
            "input", attrs={"name": re.compile(ix_name_regex)}
        )
        lab_results = soup.find_all(
            "input", attrs={"name": re.compile(ix_result_regex)}
        )

        if not (lab_names and lab_results):
            pass

    else:
        soup = BeautifulSoup(page_source, "lxml")
        lab_names = soup.find_all(
            "input", attrs={"name": re.compile(ix_name_regex)}
        )
        lab_results = soup.find_all(
            "input", attrs={"name": re.compile(ix_result_regex)}
        )

    # get unique class from first result
    if lab_names:
        hcis_class = lab_names[0]["class"]

    else:
        hcis_class = None

    lab_names = [name.get("value") for name in lab_names]
    lab_results = [result.get("value") for result in lab_results]

    labs = list(zip(lab_names, lab_results))

    # sort result for later comparision
    try:
        labs = sorted(labs, key=lambda lab: lab[0])

    except Exception:
        pass

    for lab in labs:
        if not lab_string:
            lab_string = "{}:::{}\n".format(lab[0], lab[1])

        else:
            lab_string = lab_string + "{}:::{}\n".format(lab[0], lab[1])

    return hcis_class, lab_string


def praseHN(page_source):
    soup = BeautifulSoup(page_source, "lxml")
    HNs = soup.find_all("input", attrs={"name": re.compile(r"c_hn_\d+")})

    # get hcis class
    try:
        hcis_class = HNs[0]["class"]

    except Exception:
        hcis_class = None

    HNs = [element["value"] for element in HNs]

    return hcis_class, HNs


def matchLabs(allLabs: list):
    labs = []
    for rawLab in allLabs:
        lab = {}

        # convert to AD
        date = convertToDate(rawLab[0])
        lab["date"] = date

        for regex_str in LABS_REGEX:
            matches = re.findall(regex_str[1], rawLab[1])

            if matches:
                lab[regex_str[0]] = matches[0]

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
    phoneNumbers = []

    address = (
        soup.find("input", {"id": "objdw_ex_addr_0_9"}).get("value") or ""
    )

    # phones
    phone_base_id = "objdw_ex_addr_0_"

    for x in range(14, 16):
        phone = soup.find("input", {"id": phone_base_id + str(x)}).get("value")

        if phone:
            phoneNumbers.append(phone)

    return {"phoneNumbers": phoneNumbers, "address": address}


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
