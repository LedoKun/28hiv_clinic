import atexit
import glob
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

MAX_RETRIES = os.getenv("SELENIUM_MAX_RETRIES")

SELENIUM_SERVER_URI = os.getenv("SELENIUM_SERVER_URI")
HCIS_SERVER = os.getenv("HCIS_SERVER")
HCIS_USERNAME = os.getenv("HCIS_USERNAME")
HCIS_PASSWORD = os.getenv("HCIS_PASSWORD")
HCIS_SID = os.getenv("HCIS_SID")

NHSO_USERNAME = os.getenv("NHSO_USERNAME")
NHSO_PASSWORD = os.getenv("NHSO_PASSWORD")

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)


def load_hn_list():
    patient_list_file = Path("./patient_list.json")

    if not patient_list_file.is_file():
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

                patient_list = hcis.getPatientList()

                with open(patient_list_file, "w") as file:
                    json.dump(patient_list, file)

                break

            except Exception:
                traceback.print_exc()

                if retries_count > MAX_RETRIES:
                    logger.error("Unable to get HNs, exiting.")

                    break

            finally:
                try:
                    hcis.quit()

                except WebDriverException:
                    traceback.print_exc()
                    logger.error("Lost connection with IE Webdriver.")

    else:
        with open(patient_list_file, "r") as file:
            patient_list = json.load(file)

    return patient_list


def selenium_task(worker_id, hn_list):
    """Worker code"""
    patient_information_file = Path(f"./patient_info_{worker_id}.json")
    hn_imported_file = Path(f"./imported_hn_{worker_id}.json")
    patient_failed_file = Path(f"./patient_failed_{worker_id}.json")

    # create file if not exists
    patient_information_file.touch()
    hn_imported_file.touch()
    patient_failed_file.touch()

    with open(hn_imported_file, "r") as file:
        try:
            hn_imported = json.load(file)
        except ValueError:
            hn_imported = []

    with open(patient_information_file, "r") as file:
        try:
            patient_information = json.load(file)
        except ValueError:
            patient_information = []

    hn_failed = []

    hcis = HCISImporter(
        seleniumServerURI=SELENIUM_SERVER_URI,
        hcis_server=HCIS_SERVER,
        hcis_username=HCIS_USERNAME,
        hcis_password=HCIS_PASSWORD,
        hcis_sid=HCIS_SID,
    )

    for hn in hn_list:
        if hn in hn_imported:
            continue

        remaining = len(hn_list) - len(hn_imported) - len(hn_failed)

        logger.info(
            f"[{worker_id}] "
            f"Current progress -- Imported: {len(hn_imported)}"
            f", Failed: {len(hn_failed)}, "
            f"Remaining: {remaining}"
        )
        logger.info(
            f"[{worker_id}] " "Importing patient HN {} from HCIS.".format(hn)
        )
        retries_count = 0

        patient_detail = {
            "visits": None,
            "ix": None,
            "med": None,
            "dermographic": None,
        }

        while retries_count <= MAX_RETRIES:
            try:
                retries_count = retries_count + 1

                if patient_detail["visits"] is None:
                    patient_detail["visits"] = hcis.getVisits(hn)

                if patient_detail["ix"] is None:
                    patient_detail["ix"] = hcis.getInvestigations(hn)

                if patient_detail["med"] is None:
                    patient_detail["med"] = hcis.getMedications(hn)

                if patient_detail["dermographic"] is None:
                    patient_detail["dermographic"] = hcis.getDermographic(
                        hn=hn,
                        nhso_username=NHSO_USERNAME,
                        nhso_password=NHSO_PASSWORD,
                    )

                logger.info(
                    f"[{worker_id}] "
                    "Done importing patient HN {} from HCIS.".format(hn)
                )
                patient_information.append(patient_detail)
                hn_imported.append(hn)

                with open(patient_information_file, "w") as file:
                    json.dump(patient_information, file, default=str)

                with open(hn_imported_file, "w") as file:
                    json.dump(hn_imported, file, default=str)

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

            except WebDriverException:
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

            except KeyboardInterrupt:
                logger.warn(
                    f"[{worker_id}] KeyboardInterrupt "
                    "detected, terminating."
                )
                traceback.print_exc()

                try:
                    hcis.quit()

                except WebDriverException:
                    traceback.print_exc()
                    logger.error("Lost connection with IE Webdriver.")

                finally:
                    quit()

            except Exception:
                logger.error(
                    f"[{worker_id}] Unexpected error detected,"
                    " see the traceback below."
                )
                traceback.print_exc()

            finally:
                if retries_count > MAX_RETRIES:
                    logger.error(
                        f"[{worker_id}] "
                        "Unable to get information for {}, skipping.".format(
                            hn
                        )
                    )
                    hn_failed.append(hn)

                    with open(patient_failed_file, "w") as file:
                        json.dump(hn_failed, file, default=str)

                    break

    try:
        hcis.quit()

    except Exception:
        pass

    return True


def exit_handler(pool):
    pool.close()
    pool.terminate()
    pool.join()
    quit()


if __name__ == "__main__":
    HNs = load_hn_list()

    ITERATION_COUNT = multiprocessing.cpu_count()
    count_per_iteration = len(HNs) / float(ITERATION_COUNT)

    pool = multiprocessing.Pool(processes=ITERATION_COUNT)

    # register exit handler
    atexit.register(exit_handler, pool=pool)

    for i in range(0, ITERATION_COUNT):
        list_start = int(count_per_iteration * i)
        list_end = int(count_per_iteration * (i + 1))
        worker_data_list = HNs[list_start:list_end]

        logger.info(
            f"Starting worker id {i} with data list"
            f" of size {len(worker_data_list)} entries."
        )

        pool.apply_async(selenium_task, args=(i, worker_data_list))

    pool.close()
    pool.join()

    imported_files = glob.glob("patient_info_*")
    all_patient_info = []

    for imported_file in imported_files:
        with open(imported_file) as file:
            try:
                all_patient_info = all_patient_info + json.load(file)
            except ValueError:
                pass

    all_patient_information_file = Path(f"./all_patient_info.json")
    all_patient_information_file.touch()

    with open(all_patient_information_file, "w") as file:
        json.dump(list(all_patient_info), file)
