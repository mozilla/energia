import os
import argparse
import json
import platform
import zmq
import time
import pickle

from wrappers.PowerGadget import PowerGadget
from wrappers.BLA import BLA
from browser import Browser
from time import sleep
from pandas import DataFrame, concat
from server import Server

class Benchmark:
    def __init__(self, args):
        self._args = args

        with open(args.config) as f:
            self._config = json.load(f)

    def log(self):
        df = None
        for page in self._get_pages():
            for browser in self._get_browsers():
                df = self._run_iteration(df, page, browser)

        return df.sort(['OS', 'Page', 'Browser'])

    def _run_iteration(self, df, page, browser):
        browser = Browser.create_browser(name=browser["name"], path=browser["path"], page=page)
        args.image = os.path.basename(browser.get_path())
        browser.initialize()
        partial = None
        sleep(self._args.sleep)

        for benchmark in self._get_benchmarks():
            try:
                benchmark = Benchmark._create_benchmark(benchmark, self._args)
                partial = self._run_benchmark(benchmark, browser, partial)
            except:
                print("Warning: benchmark {} not supported".format(benchmark))

        browser.finalize()
        return partial if df is None else concat([df, partial])

    def _run_benchmark(self, benchmark, browser, partial):
        df = benchmark.log()
        df['Browser'] = browser.get_name()
        df['Page'] = browser.get_page()
        df['OS'] = browser.get_os()

        res = df if partial is None else partial.combine_first(df)
        return res

    @staticmethod
    def _create_benchmark(benchmark, args):
        if benchmark == "PowerGadget":
            return PowerGadget(args)
        elif benchmark == "BLA":
            return BLA(args)
        else:
            raise Exception("Benchmark not found")

    def _get_pages(self):
        return self._config["Pages"]

    def _get_browsers(self):
        os = platform.system()
        return self._config["OS"][os]

    def _get_benchmarks(self):
        return self._config["Benchmarks"]

class ClientBenchmark(Benchmark):
    def __init__(self, args):
        self._context = zmq.Context()
        self._scatter_socket = self._context.socket(zmq.PULL)
        self._gather_socket = self._context.socket(zmq.PUSH)

        ports = {"Windows": 9000, "Darwin": 9001, "Linux": 9002}
        self._scatter_socket.connect("tcp://{}:{}".format(args.address, ports[platform.system()]))
        self._gather_socket.connect("tcp://{}:9003".format(args.address))

    def log(self):
        while True:
            msg = pickle.loads(self._scatter_socket.recv())
            self._args = msg["args"]
            self._config = msg["config"]
            page = msg["page"]
            browser = msg["browser"]

            print("Processing request for {} on {}".format(page, browser["name"]))
            df = self._run_iteration(None, page, browser)
            self._gather_socket.send(pickle.dumps(df))

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Desktop Browser Power benchmarking Utility",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms, if applicable", default=100, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=10, type=int)
    parser.add_argument("-o", "--output", help="Path of the final csv output", default="report.csv")
    parser.add_argument("-p", "--path", help="Tool path", default="")
    parser.add_argument("-b", "--benchmark", help="Benchmark to run", default="idle")
    parser.add_argument("-c", "--config", help="Configuration file", default="config.json")
    parser.add_argument("-s", "--sleep", help="Seconds to sleep before the benchmarks start recording", default=120, type=int)
    parser.add_argument("-r", "--is_server", help="True if instance is a server", dest="is_server", action="store_true")
    parser.add_argument("-a", "--address", help="Server address", default=None)

    parser.set_defaults(is_server=False)
    args = parser.parse_args()
    args.image = None
    df = None

    if args.is_server:
        server = Server(args)
        df = server.run()
    else:
        benchmark = None

        if args.benchmark == "idle":
            if args.address is None:
                benchmark = Benchmark(args)
            else:
                benchmark = ClientBenchmark(args)
        elif args.benchmark == "PowerGadget":
            benchmark = PowerGadget(args)
        elif args.benchmark == "BLA":
            benchmark = BLA(args)
        else:
            raise Exception("Benchmark not found")

        df = benchmark.log()

    if df is not None:
        df.to_csv(args.output, float_format="%.3f")
    else:
        print("Warning: no output produced")
