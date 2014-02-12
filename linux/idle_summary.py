import argparse
import json
import platform
import os

from time import sleep
from subprocess import Popen, PIPE
from pandas import DataFrame
from power_summary import PowerSummary

_fields = []
_config = None
_args = None
_output = None
_result_df = None

class IdleSummary(PowerSummary):
    def __init__(self, browser, duration, iterations):
        super().__init__(duration, iterations)
        self._browser = browser

    def initialize(self):
        self._browser.initialize()
        sleep(_args.sleep)

    def process_measurements(self, df):
        global _result_df
        summary = df.mean().to_dict()
        stds = df.std().to_dict()

        for key, value in stds.items():
            summary[key+" SD"] = value

        summary["Browser"] = self._browser.get_name()
        summary["Page"] = self._browser.get_page()
        _result_df = _result_df.append(summary, ignore_index=True)

    def finalize(self):
        self._browser.finalize()
        sleep(5)

class Browser:
    def __init__(self, name, path, page):
        self.page = page
        self.browser = path
        self.description = name

    def get_name(self):
        return self.description

    def get_page(self):
        return self.page

    @staticmethod
    def create_browser(name, path, page):
        os = platform.system()

        if os == "Linux":
            return UbuntuBrowser(name, path, page)
        else:
            assert(0)

class UbuntuBrowser(Browser):
    def __init__(self, name, path, page):
        super().__init__(name, path, page)

    def initialize(self):
        os.system(self.browser + " " + self.page + "&")

    def finalize(self):
        if self.browser == "chromium-browser":
            os.system("wmctrl -c Chromium")
        elif self.browser == "firefox-trunk":
            os.system("wmctrl -c Nightly")
        else:
            os.system("wmctrl -c " + self.browser)

def get_pages():
    return _config["Pages"]

def get_browsers():
    os = platform.system()
    return _config["OS"][os]

def run_benchmark():
    for page in get_pages():
        for b in get_browsers():
            browser = Browser.create_browser(name=b["name"], path=b["path"], page=page)
            idleSummary = IdleSummary(browser, _args.duration, _args.iterations)
            idleSummary.log()

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Idle power benchmark",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=10, type=int)
    parser.add_argument("-o", "--output", help="Path of the csv output", default="report.csv")
    parser.add_argument("-c", "--config", help="Configuration file", default="idle_config.json")
    parser.add_argument("-s", "--sleep", help="Seconds to sleep before the benchmark starts recording the power usage", default=100, type=int)
    _args = parser.parse_args()

    # Prepare result dataset
    tmp = ["%c0", "GHz", "TSC", "SMI", "%c1", "%c3", "%c6", "%c7", "CTMP",
           "PTMP", "%pc2", "%pc3", "%pc6", "%pc7", "Pkg_W", "Cor_W", "GFX_W"]
    for field in tmp:
        _fields.append(field)
        _fields.append(field + " SD")
    _fields.append("Browser")
    _fields.append("Page")
    _result_df = DataFrame(columns=_fields)

    # Load configuration
    with open(_args.config) as f:
        _config = json.load(f)

    # Run benchmark
    run_benchmark()
    _result_df.to_csv(_args.output, index=False)
