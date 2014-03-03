import os
import argparse
import json
import platform

from wrappers.PowerGadget import PowerGadget
from browser import Browser
from time import sleep
from pandas import DataFrame, concat

class Benchmark:
    def __init__(self, args):
        self._args = args #browser and 

        with open(args.config) as f:
            self._config = json.load(f)

    def log(self):
        df = None

        for page in self._get_pages():
            for browser in self._get_browsers():
                browser = Browser.create_browser(name=browser["name"], path=browser["path"], page=page)
                browser.initialize()
                partial = None
                sleep(self._args.sleep)

                for benchmark in self._get_benchmarks():
                    benchmark = Benchmark._create_benchmark(benchmark, self._args)
                    partial = self.run(benchmark, browser, partial)

                browser.finalize()
                df = partial if df is None else concat([df, partial])

        return df

    def run(self, benchmark, browser, partial):
        df = benchmark.log()
        res = df if partial is None else partial.combine_first(df)
        return res

    @staticmethod
    def _create_benchmark(benchmark, args):
        if benchmark == "PowerGadget":
            return PowerGadget(args)
        else:
            raise Exception("Benchmark not found")

    def _get_pages(self):
        return self._config["Pages"]

    def _get_browsers(self):
        os = platform.system()
        return self._config["OS"][os]

    def _get_benchmarks(self):
        return self._config["Benchmarks"]

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="External browser benchmark suite",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms, if applicable", default=50, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=5, type=int)
    parser.add_argument("-o", "--output_csv", help="Path of the final csv output", default="report.csv")
    parser.add_argument("-l", "--plot", help="Path of the final plot, if applicable", default="report.png")
    parser.add_argument("-p", "--path", help="Tool path", default="")
    parser.add_argument("-b", "--benchmark", help="Benchmark to run", default="idle")
    parser.add_argument("-c", "--config", help="Configuration file", default="config.json")
    parser.add_argument("-s", "--sleep", help="Seconds to sleep before the benchmarks start recording", default=100, type=int)
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    benchmark = None
    if args.benchmark == "idle":
        benchmark = Benchmark(args)
    elif args.benchmark == "PowerGadget":
        benchmark = PowerGadget(args)

    df = benchmark.log()
    df.to_csv(args.output_csv)
