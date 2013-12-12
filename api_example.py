import os
import time

from power_logger import PowerLogger
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class CnnLoad(PowerLogger):
    def __init__(self):
        super().__init__()
        self._driver = webdriver.Firefox()

    # This method is run before the power profiling is enabled
    def initialize_iteration(self):
        self._driver.get("about:blank")

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        self._driver.get("http://www.cnn.com")
        # Mark an event in time that will appear in the final plots
        self.add_marker("page load")
        self._driver.get("http://www.cnn.com")
        self.add_marker("page load")
        self._driver.get("http://www.cnn.com")
        self.add_marker("page load")

    # This method is run after the power profiling has been disabled
    def finalize_iteration(self):
        self._driver.get("about:blank")

logger = CnnLoad()
logger.log(50, 5)
