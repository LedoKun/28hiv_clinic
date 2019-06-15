from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

from .hcis_helpers import (
    clickNew,
    encodeStr,  # convertToDate,
    isElementPresent,
    isNextPageLinkExists,
    matchLabs,
    praseDermographic,
    praseDermographicTab2,
    praseHN,
    praseInvestigation,
    praseMedication,
    praseTwoTablePage,
    praseVisits,
    searchHN,
    setInputDate,
    waitForLoad,
)
from .importer import Importer

CLINIC_NAME = "วัณโรค"
CLINIC_ID = "111"

EXPLICIT_WAIT = 10


class HCISImporter(Importer):
    def __init__(
        self,
        seleniumServerURI: str,
        hcis_server: str,
        hcis_username: str,
        hcis_password: str,
        hcis_sid: str,
        hcis_client_name: str = "pc0001",
        hcis_client_ip: str = "127.0.0.1",
        hcis_client_mac: str = "6D:53:85:EF:85:53",
        desired_capabilities: DesiredCapabilities = None,
        set_page_load_timeout: int = 30,
    ):

        # IE DesiredCapabilities
        caps = DesiredCapabilities.INTERNETEXPLORER
        # caps['ignoreProtectedModeSettings'] = True
        caps["nativeEvents"] = False
        # caps['requireWindowFocus'] = True
        # caps['INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS'] = True
        # caps["se:ieOptions"] = {}
        # caps["se:ieOptions"]["ie.forceCreateProcessApi"] = True
        # caps["se:ieOptions"]["ie.browserCommandLineSwitches"] = "-private"
        # caps["se:ieOptions"]["ie.ensureCleanSession"] = True

        self.driver = webdriver.Remote(
            command_executor=seleniumServerURI,
            desired_capabilities=desired_capabilities
            if desired_capabilities
            else caps,
        )

        self.driver.set_page_load_timeout(set_page_load_timeout)
        self.server = hcis_server
        self.username = encodeStr(hcis_username)
        self.password = encodeStr(hcis_password)
        self.sid = hcis_sid

        self.client_name = hcis_client_name
        self.client_ip = hcis_client_ip
        self.client_mac = hcis_client_mac

    def getDermographic(self, hn: str, nhso_username, nhso_password) -> dict:
        url = (
            f"http://{self.server}/hcis_but01/Default.aspx?PBCommandParm="
            + f"userid={self.username}|passwd={self.password}|sid={self.sid}|"
            + "frmname={}|nhso_user={}|nhso_pass={}|".format(
                "opd", nhso_username, nhso_password
            )
            + f"hostname={self.client_name}|ipaddr={self.client_ip}|"
            + f"macaddr={self.client_mac}|srvname={self.server}|"
        )

        self.driver.delete_all_cookies()
        self.driver.get(url)

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        # get current hn
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        current_hn = soup.find("span", {"id": "objdw_lupt_0_0"})

        if current_hn:
            # new patient
            new_patient_button_css = "img[src*='exit_enab_32x32.gif']"
            new_patient_button = WebDriverWait(
                self.driver, EXPLICIT_WAIT
            ).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, new_patient_button_css)
                )
            )
            new_patient_button.click()

            # wait
            waitForLoad(self.driver)

        # checkbox search by hn
        hn_checkbox = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, "objdw_head_0_2"))
        )
        hn_checkbox.click()

        # wait
        waitForLoad(self.driver)

        # search for the patient
        text_box_id = "objdw_head_0_4"
        searchHN(driver=self.driver, text_box_id=text_box_id, hn=hn)

        # wait
        waitForLoad(self.driver)

        # load patient details
        details_botton_name = "b_1_0"
        if isElementPresent(
            driver=self.driver, by="name", value=details_botton_name
        ):
            details_botton = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.element_to_be_clickable((By.NAME, details_botton_name))
            )
            details_botton.click()

            # wait
            waitForLoad(self.driver)

        # wait
        WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.visibility_of_element_located((By.NAME, "t_privilegedsp_0"))
        )

        dermographic = praseDermographic(
            page_source=self.driver.page_source, hn=hn
        )

        # go to second tab
        tab_id = "WW_1_C_tab_1_1"
        tab = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, tab_id))
        )
        tab.click()

        # wait
        waitForLoad(self.driver)

        dermographicTab2 = praseDermographicTab2(
            page_source=self.driver.page_source
        )

        dermographic["phoneNumbers"] = dermographicTab2["phoneNumbers"]

        # extract info
        return dermographic

    def getVisits(self, hn: str) -> list:
        url = (
            f"http://{self.server}/hcis_cnifcn/default.aspx?PBCommandParm="
            + f"userid={self.username}|passwd={self.password}|"
            + f"sid={self.sid}|hostname={self.client_name}|"
            + f"ipaddr={self.client_ip}|macaddr={self.client_mac}|"
            + f"srvname={self.server}|"
        )

        self.driver.delete_all_cookies()
        self.driver.get(url)

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        clickNew(self.driver)

        # wait
        waitForLoad(self.driver)

        if hn not in self.driver.page_source:
            # search for the patient
            searchHN(driver=self.driver, text_box_id="objdw_lupt_0_2", hn=hn)

            # wait
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located((By.NAME, "t_privilegedsp_0"))
            )

        # prase visits
        visits = praseVisits(self.driver.page_source)

        while True:
            link = isNextPageLinkExists(driver=self.driver)

            if link:
                link.click()

                # wait
                waitForLoad(self.driver)

                visits = visits + praseVisits(self.driver.page_source)

            else:
                break

        return visits

    def getMedications(self, hn: str) -> list:
        url = (
            f"http://{self.server}/hcis_sppinq/Default.aspx"
            + f"?PBCommandParm=userid={self.username}|passwd={self.password}|"
            + f"sid={self.sid}|hostname={self.client_name}|"
            + f"ipaddr={self.client_ip}|macaddr={self.client_mac}|"
            + f"srvname={self.server}|"
        )

        self.driver.delete_all_cookies()
        self.driver.get(url)

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        clickNew(self.driver)

        # wait
        waitForLoad(self.driver)

        if hn not in self.driver.page_source:
            # search for the patient
            text_box_id = "objdw_lupt_0_2"
            searchHN(driver=self.driver, text_box_id=text_box_id, hn=hn)

            # wait
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located((By.NAME, "t_privilegedsp_0"))
            )

        # set start date
        med_start_date = "01/01/2500"
        med_start_date_input_id = "objdw_search_0_6"

        setInputDate(
            driver=self.driver,
            input_id=med_start_date_input_id,
            date_str=med_start_date,
        )

        # click search
        search_button = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, "WW_0_C_cb_1"))
        )
        search_button.click()

        # get medication list
        date_element_xpath = "//span[starts-with(@name, 'compute_2_')]"
        element_text_split_by = " "
        fnc = praseMedication

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        results = praseTwoTablePage(
            self.driver, date_element_xpath, element_text_split_by, fnc
        )

        return results

    def getInvestigations(self, hn: str) -> list:
        url = (
            f"http://{self.server}/hcis_lbresult/Default.aspx?"
            + f"PBCommandParm=userid={self.username}|passwd={self.password}|"
            + f"sid={self.sid}|hostname={self.client_name}|"
            + f"ipaddr={self.client_ip}|macaddr={self.client_mac}|"
            + f"srvname={self.server}|"
        )

        self.driver.delete_all_cookies()
        self.driver.get(url)

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        clickNew(self.driver)

        # wait
        waitForLoad(self.driver)

        # search for the patient
        if hn not in self.driver.page_source:
            text_box_id = "objdw_lupt_0_2"
            searchHN(driver=self.driver, text_box_id=text_box_id, hn=hn)

            # wait
            waitForLoad(self.driver)

        # wait
        waitForLoad(self.driver)

        # get lab list
        date_element_xpath = "//span[starts-with(@name, 'compute_1_')]"
        element_text_split_by = "::"
        fnc = praseInvestigation

        results = praseTwoTablePage(
            self.driver, date_element_xpath, element_text_split_by, fnc
        )

        prasedLabs = matchLabs(results)

        return prasedLabs

    def getPatientList(self):
        url = (
            f"http://{self.server}/hcis_nrsque/Default.aspx"
            + f"?PBCommandParm=userid={self.username}|passwd={self.password}|"
            + f"sid={self.sid}|hostname={self.client_name}|"
            + f"ipaddr={self.client_ip}|macaddr={self.client_mac}|"
            + f"srvname={self.server}|"
        )

        self.driver.delete_all_cookies()
        self.driver.get(url)

        # wait
        waitForLoad(self.driver, wait_for_dom=True)

        clickNew(self.driver)

        clicnic_select_id = "objdw_ext_cnq_0_6"
        clicnic_input_name = "c_section_0"

        # wait
        waitForLoad(self.driver)

        # select clinic
        clinic_select = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, clicnic_select_id))
        )
        clinic_select = Select(clinic_select)
        clinic_select.select_by_visible_text(CLINIC_NAME)

        # allow js blur effect to run
        clinic_select = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, clicnic_select_id))
        )
        clinic_select.send_keys(Keys.TAB)

        # wait for the form to update
        WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.text_to_be_present_in_element_value(
                (By.NAME, clicnic_input_name), CLINIC_ID
            )
        )

        # set start date
        start_date = "01/01/2500"
        start_date_id = "objdw_ext_cnq_0_1"

        setInputDate(
            driver=self.driver, input_id=start_date_id, date_str=start_date
        )

        # wait
        waitForLoad(self.driver)

        # set patient status
        patient_status_input_name = "c_ovstost_0"
        patient_status_id = "objdw_ext_ovstost_0_2"
        patient_status = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, patient_status_id))
        )

        patient_status_select = Select(patient_status)
        patient_status_select.select_by_value("")

        # allow js blur effect to run
        patient_status = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, patient_status_id))
        )
        patient_status.send_keys(Keys.TAB)

        # wait for the form to update
        patient_status_input = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.visibility_of_element_located(
                (By.NAME, patient_status_input_name)
            )
        )
        patient_status_input.send_keys("" + Keys.TAB)

        # # wait for the form to update
        # WebDriverWait(self.driver, EXPLICIT_WAIT).until(
        #     EC.text_to_be_present_in_element_value(
        #         (By.NAME, patient_status_input_name), ""
        #     )
        # )

        # click search
        search_icon_css = "img[src*='find_enab_32x32.gif']"
        search_icon = WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, search_icon_css))
        )
        search_icon.click()

        # wait
        waitForLoad(self.driver)

        # read hn
        HNs = praseHN(self.driver.page_source)

        while True:
            link = isNextPageLinkExists(driver=self.driver)

            if link:
                link.click()
                HNs = HNs + praseHN(self.driver.page_source)

            else:
                if HNs:
                    break

        return list(set(HNs))

    def quit(self):
        self.driver.quit()

    def testAlive(self):
        return self.driver.title
