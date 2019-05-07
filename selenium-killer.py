import logging
import os
import sys
import time

# kill processes every two hours
SLEEP_TIME_SEC = 3600

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)


def killer():
    while True:
        logger.info(f"Start counting down {SLEEP_TIME_SEC} seconds.")
        time.sleep(SLEEP_TIME_SEC)

        # kill selenium webdriver
        logger.info("Killing IEWebDriver processes.")
        os.system("taskkill /f /im IEDriverServer.exe")

        # kill IE processes
        logger.info("Killing IE processes.")
        os.system("taskkill /F /IM iexplore.exe")


if __name__ == "__main__":
    killer()
