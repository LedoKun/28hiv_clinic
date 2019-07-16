import json
import logging
import multiprocessing
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from selenium.common.exceptions import (
    ElementNotVisibleException,
    JavascriptException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

# from patient_importer.hcis_importer import HCISImporter
from hivclinic.helpers.patient_importer.hcis_importer import HCISImporter

# Config
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Multiprocessing config
ITERATION_COUNT = multiprocessing.cpu_count()

# Selenium config
MAX_RETRIES = os.getenv("SELENIUM_MAX_RETRIES")

SELENIUM_SERVER_URI = os.getenv("SELENIUM_SERVER_URI")
HCIS_SERVER = os.getenv("HCIS_SERVER")
HCIS_USERNAME = os.getenv("HCIS_USERNAME")
HCIS_PASSWORD = os.getenv("HCIS_PASSWORD")
HCIS_SID = os.getenv("HCIS_SID")

NHSO_USERNAME = os.getenv("NHSO_USERNAME")
NHSO_PASSWORD = os.getenv("NHSO_PASSWORD")

# File paths
HN_LIST_FILE = "./hn_list.json"
IMPORTED_HN_FILE = "./imported_hn.json"
IMPORTED_INFORMATION = "./patient_details.json"

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)


def start_workers():
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    result_list = manager.list()
    hn_imported = manager.list()
    result_lock = manager.Lock()

    pool = multiprocessing.Pool(processes=ITERATION_COUNT)

    # get hn list
    with open(HN_LIST_FILE, "r") as file:
        try:
            hn_list = json.load(file)

        except Exception:
            hn_list = []

    if not hn_list:
        hn_list = hn_list_scraper()

    # get imported hn
    with open(IMPORTED_HN_FILE, "r") as file:
        try:
            imported_hn_list = json.load(file)

        except Exception:
            imported_hn_list = []

    hn_list = list(set(hn_list) - set(imported_hn_list))

    # prepare queue
    for hn in hn_list:
        queue.put(hn)

    # add list of imported hn
    for hn in imported_hn_list:
        hn_imported.append(hn)

    # add imported information into the list
    with open(IMPORTED_INFORMATION, "r") as file:
        try:
            imported_patients = json.load(file)

        except Exception:
            imported_patients = []

    for imported_patient in imported_patients:
        result_list.append(imported_patient)

    # start workers
    try:
        for worker_id in range(ITERATION_COUNT):
            pool.apply_async(
                selenium_task,
                args=(worker_id, queue, hn_imported, result_list, result_lock),
            )

    except KeyboardInterrupt:
        logger.warning("[Main] Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        pool.join()

    else:
        logger.info("[Main] Task finished, terminating")
        pool.close()
        pool.join()


def hn_list_scraper():
    logger.info("[Main] Scraping HN list.")

    retries_count = 1

    while retries_count <= MAX_RETRIES:
        try:
            retries_count = retries_count + 1

            hcis = HCISImporter(
                seleniumServerURI=SELENIUM_SERVER_URI,
                hcis_server=HCIS_SERVER,
                hcis_username=HCIS_USERNAME,
                hcis_password=HCIS_PASSWORD,
                hcis_sid=HCIS_SID,
            )

            hn_list = hcis.getPatientList()

            with open(HN_LIST_FILE, "w") as file:
                json.dump(hn_list, file)

            break

        except Exception:
            traceback.print_exc()

            if retries_count > MAX_RETRIES:
                logger.error("Unable to get HNs, exiting.")
                quit()

        finally:
            try:
                hcis.quit()

            except WebDriverException:
                traceback.print_exc()
                logger.error("Lost connection with IE Webdriver.")

    return hn_list


def selenium_task(worker_id, queue, hn_imported, result_list, result_lock):
    logger.info(f"[{worker_id}] Starting...")

    hcis = HCISImporter(
        seleniumServerURI=SELENIUM_SERVER_URI,
        hcis_server=HCIS_SERVER,
        hcis_username=HCIS_USERNAME,
        hcis_password=HCIS_PASSWORD,
        hcis_sid=HCIS_SID,
    )

    while not queue.empty():
        current_hn = queue.get()

        patient_details = {
            "visits": None,
            "ix": None,
            "med": None,
            "dermographic": None,
        }
        retries_count = 1

        with result_lock:
            logger.info(
                f"[{worker_id}] Importing HN {current_hn} "
                f"(Done {len(list(hn_imported))} - "
                f"Remaining {queue.qsize()})"
            )

        while retries_count <= MAX_RETRIES:
            retries_count = retries_count + 1

            try:
                if patient_details["ix"] is None:
                    logger.info(
                        f"[{worker_id}] Importing investigations of "
                        f"HN {current_hn} from HCIS."
                    )
                    patient_details["ix"] = hcis.getInvestigations(current_hn)

                if patient_details["med"] is None:
                    logger.info(
                        f"[{worker_id}] Importing medications of "
                        f"HN {current_hn} from HCIS."
                    )
                    patient_details["med"] = hcis.getMedications(current_hn)

                if patient_details["dermographic"] is None:
                    logger.info(
                        f"[{worker_id}] Importing dermographics of "
                        f"HN {current_hn} from HCIS."
                    )
                    patient_details["dermographic"] = hcis.getDermographic(
                        hn=current_hn,
                        nhso_username=NHSO_USERNAME,
                        nhso_password=NHSO_PASSWORD,
                    )

                if patient_details["visits"] is None:
                    logger.info(
                        f"[{worker_id}] Importing visits of HN "
                        f"{current_hn} from HCIS."
                    )
                    cares, patient_details["visits"] = hcis.getVisits(
                        current_hn
                    )

                    # add hospitals names in dermographics
                    patient_details["dermographic"]["cares"] = cares

                logger.info(
                    f"[{worker_id}] Done importing patient HN "
                    f"{current_hn} from HCIS."
                )

                with result_lock:
                    hn_imported.append(current_hn)
                    result_list.append(patient_details)

                    # write results to file
                    with open(IMPORTED_HN_FILE, "w") as file:
                        json.dump(list(hn_imported), file)

                    with open(IMPORTED_INFORMATION, "w") as file:
                        json.dump(list(result_list), file)

                break

            except (
                ElementNotVisibleException,
                NoSuchElementException,
                StaleElementReferenceException,
                TimeoutException,
                JavascriptException,
            ):
                logger.error(
                    f"[{worker_id}] Error detected, see the traceback"
                    " below, reloading the page."
                )
                traceback.print_exc()

            except Exception:
                logger.error(
                    f"[{worker_id}] Error detected,"
                    " see the traceback below."
                )
                traceback.print_exc()

                # the web driver is lost/dead
                logger.error(
                    f"[{worker_id}] Dectected problems "
                    "with IEWebDriver, restarting."
                )

                try:
                    hcis.quit()

                except Exception:
                    pass

                finally:
                    hcis = HCISImporter(
                        seleniumServerURI=SELENIUM_SERVER_URI,
                        hcis_server=HCIS_SERVER,
                        hcis_username=HCIS_USERNAME,
                        hcis_password=HCIS_PASSWORD,
                        hcis_sid=HCIS_SID,
                    )

                logger.info(f"[{worker_id}] Recovered from error.")

            finally:
                if retries_count > MAX_RETRIES:
                    logger.error(
                        f"[{worker_id}] Unable to get information "
                        f"for HN {current_hn}, putting the HN "
                        "at the end of the queue."
                    )

                    queue.put(current_hn)

                    break

    try:
        hcis.quit()

    except Exception:
        pass

    return True


def create_files():
    hn_list_file = Path(HN_LIST_FILE)
    hn_list_file.touch()

    imported_hn_file = Path(IMPORTED_HN_FILE)
    imported_hn_file.touch()

    imported_information_file = Path(IMPORTED_INFORMATION)
    imported_information_file.touch()


if __name__ == "__main__":
    create_files()
    start_workers()
