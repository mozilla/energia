import os
import time

from power_logger import PowerLogger
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class CnnLoad(PowerLogger):
    def __init__(self):
        super().__init__(debug=True)
        self._driver = webdriver.Firefox()

    def initialize_iteration(self):
        pass

    def execute_iteration(self):
        self.add_marker("start")
        self._driver.get("http://www.cnn.com")
        self._driver.get("http://www.cnn.com")
        self._driver.get("http://www.cnn.com")
        self._driver.get("about:blank")
        self.add_marker("finish")

    def finalize_iteration(self):
        pass

logger = CnnLoad()
logger.log(50, 2, 10)
