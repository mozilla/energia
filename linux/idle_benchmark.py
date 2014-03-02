import argparse
import json
import platform
import os
import power_summary as ps

sys.path.append("..")

from browser import Browser
from time import sleep
from subprocess import Popen, PIPE
from pandas import DataFrame

_fields = []
_config = None
_args = None
_output = None
_result_df = None

class IdleSummary(ps.PowerSummary):
    def __init__(self, browser, duration, iterations):
        super().__init__(duration, iterations)
        self._browser = browser

    def initialize(self):
        self._browser.initialize()
        sleep(_args.sleep)

    def process_measurements(self, df):
        global _result_df
        summary = df.mean().to_dict()
        cis = df.apply(lambda x: stats.sem(x) * stats.t.ppf((1.95)/2., len(x) - 1)).to_dict()

        for key, value in cis.items():
            summary[key+" CI"] = value

        summary["Browser"] = self._browser.get_name()
        summary["Page"] = self._browser.get_page()
        _result_df = _result_df.append(summary, ignore_index=True)

    def finalize(self):
        self._browser.finalize()
        sleep(5)

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
    for field in ps.fields:
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
