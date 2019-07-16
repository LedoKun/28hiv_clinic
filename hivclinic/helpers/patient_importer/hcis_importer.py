from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from .hcis_helpers import encodeStr  # isElementPresent,; convertToDate,
from .hcis_helpers import (
    clickNew,
    isNextPageLinkExists,
    isDisplayPatientInfo,
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
    waitForPageReady,
    waitForHNToLoaded,
)
from .importer import Importer

CLINIC_NAME = "วัณโรค"
CLINIC_ID = "111"

EXPLICIT_WAIT = 15


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
        caps["nativeEvents"] = False

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
        self.wait = WebDriverWait(self.driver, EXPLICIT_WAIT)

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
        waitForPageReady(wait=self.wait)
        old_source = self.driver.page_source

        while isDisplayPatientInfo(driver=self.driver, wait=self.wait):
            clickNew(self.wait, False)

            # wait
            self.wait.until(
                (
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                    and (d.page_source != old_source)
                )
            )

        # search for the patient
        text_box_css = "#objdw_head_0_4"
        searchHN(wait=self.wait, text_box_css=text_box_css, hn=hn)

        # wait
        waitForPageReady(wait=self.wait)

        # load patient details
        details_botton_css = "input[name='b_1_0']"
        details_botton = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, details_botton_css))
        )
        details_botton.click()

        # wait
        waitForHNToLoaded(self.wait, hn)

        dermographic = praseDermographic(
            page_source=self.driver.page_source, hn=hn
        )

        # go to second tab
        tab_css_selector = "div[id$=_C_tab_1_1]"
        tab = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, tab_css_selector))
        )
        tab.click()

        # wait
        self.wait.until(
            EC.presence_of_element_located((By.ID, "objdw_ex_addr_0_0"))
        )

        dermographicTab2 = praseDermographicTab2(
            page_source=self.driver.page_source
        )

        dermographic["address"] = dermographicTab2["address"]
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
        waitForPageReady(wait=self.wait)
        old_source = self.driver.page_source

        while isDisplayPatientInfo(driver=self.driver, wait=self.wait):
            clickNew(self.wait)

            # wait
            self.wait.until(
                (
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                    and (d.page_source != old_source)
                )
            )

        # search for the patient
        searchHN(wait=self.wait, text_box_css="#objdw_lupt_0_2", hn=hn)

        # wait
        waitForHNToLoaded(self.wait, hn)

        # prase visits
        cares, visits = praseVisits(self.driver.page_source)

        while True:
            link = isNextPageLinkExists(driver=self.driver, wait=self.wait)
            old_source = self.driver.page_source

            if link:
                link.click()

                # wait
                self.wait.until(
                    (
                        lambda d: d.execute_script(
                            "return document.readyState"
                        )
                        == "complete"
                        and (d.page_source != old_source)
                    )
                )

                _, new_page_visits = praseVisits(self.driver.page_source)

                visits = visits + new_page_visits

            else:
                break

        return cares, visits

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
        waitForPageReady(wait=self.wait)
        old_source = self.driver.page_source

        while isDisplayPatientInfo(driver=self.driver, wait=self.wait):
            clickNew(self.wait)

            # wait
            self.wait.until(
                (
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                    and (d.page_source != old_source)
                )
            )

        # search for the patient
        text_box_css = "#objdw_lupt_0_2"
        searchHN(wait=self.wait, text_box_css=text_box_css, hn=hn)

        # wait
        waitForHNToLoaded(self.wait, hn)

        # set start date
        med_start_date = "01/01/2500"
        med_start_date_input_id = "objdw_search_0_6"

        setInputDate(
            wait=self.wait,
            input_id=med_start_date_input_id,
            date_str=med_start_date,
        )

        # click search
        search_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "WW_0_C_cb_1"))
        )
        old_source = self.driver.page_source
        search_button.click()

        # get medication list
        date_element_css = "span[name^='compute_2_']"
        element_text_split_by = " "
        fnc = praseMedication

        # wait
        self.wait.until(
            (
                lambda d: d.execute_script("return document.readyState")
                == "complete"
                and (d.page_source != old_source)
            )
        )

        results = praseTwoTablePage(
            driver=self.driver,
            wait=self.wait,
            date_element_css=date_element_css,
            element_text_split_by=element_text_split_by,
            elementsPraser=fnc,
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
        waitForPageReady(wait=self.wait)
        old_source = self.driver.page_source

        while isDisplayPatientInfo(driver=self.driver, wait=self.wait):
            clickNew(self.wait)

            # wait
            self.wait.until(
                (
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                    and (d.page_source != old_source)
                )
            )

        # search for the patient
        text_box_css = "#objdw_lupt_0_2"
        searchHN(wait=self.wait, text_box_css=text_box_css, hn=hn)

        # get lab list
        date_element_css = "span[name^='compute_1_']"
        element_text_split_by = "::"
        fnc = praseInvestigation

        # wait again
        waitForHNToLoaded(self.wait, hn)

        results = praseTwoTablePage(
            driver=self.driver,
            wait=self.wait,
            date_element_css=date_element_css,
            element_text_split_by=element_text_split_by,
            elementsPraser=fnc,
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
        waitForPageReady(wait=self.wait)

        while True:
            clickNew(self.wait)

            # wait
            waitForPageReady(wait=self.wait)

            # get value of clinic
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            clinic_id = soup.find(
                "input", {"id": "objdw_ext_ovstost_0_1"}
            ).get("value")

            if not clinic_id:
                break

        # set start date
        start_date = "01/01/2500"
        start_date_id = "objdw_ext_cnq_0_1"

        setInputDate(
            wait=self.wait, input_id=start_date_id, date_str=start_date
        )

        # select clinic
        clicnic_select_id = "objdw_ext_cnq_0_6"
        clicnic_input_name = "c_section_0"

        clinic_select = self.wait.until(
            EC.element_to_be_clickable((By.ID, clicnic_select_id))
        )
        clinic_select = Select(clinic_select)
        clinic_select.select_by_visible_text(CLINIC_NAME)

        # allow js blur effect to run
        clinic_select = self.wait.until(
            EC.element_to_be_clickable((By.ID, clicnic_select_id))
        )
        clinic_select.send_keys(Keys.TAB)

        # wait for the form to update
        self.wait.until(
            EC.text_to_be_present_in_element_value(
                (By.NAME, clicnic_input_name), CLINIC_ID
            )
        )

        # click search
        search_icon_css = "img[src$='find_enab_32x32.gif']"
        search_icon = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, search_icon_css))
        )
        search_icon.click()

        # wait
        waitForPageReady(wait=self.wait)

        # read hn
        HNs = praseHN(self.driver.page_source)

        while True:
            link = isNextPageLinkExists(driver=self.driver, wait=self.wait)

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
