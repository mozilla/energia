import argparse
import tempfile
import os
import uuid
import shutil
import re

from subprocess import Popen, PIPE
from pandas import DataFrame

fields = ["%c0", "GHz", "TSC", "SMI", "%c1", "%c3", "%c6", "%c7", "CTMP",
          "PTMP", "%pc2", "%pc3", "%pc6", "%pc7", "Pkg_W", "Cor_W", "GFX_W", "wakeups"]

class PowerTop:
    def __init__(self, duration=5):
        self._process = None
        self._duration = duration
        self._file = tempfile.NamedTemporaryFile(suffix=".csv", delete='False')

    def _remove_tmp_dir(self, directory):
        shutil.rmtree(directory)

    def start(self):
        self._process = Popen(["powertop --csv={} --time={}".format(self._file.name, self._duration)],
                              shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def join(self):
        self._process.wait()

        with open(self._file.name, "r") as f:
            content = f.read()
            match = re.search(r'\n(.*),(.*) wakeups/second', content)
            if match:
                return int(match.group(1))
            else:
                assert(0)

class TurboStat:
    def __init__(self, duration=5):
        self._process = None
        self._duration = duration

    def start(self):
        self._process = Popen(['turbostat -S sleep ' + str(self._duration)],
                              shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def join(self):
        out = self._process.communicate()
        f = out[1].decode().split('\n')[1].split()
        summary = {}
        for i, val in enumerate(fields[:-1]):
            summary[val] = f[i]
        return summary

class PowerSummary:
    def __init__(self, duration, iterations, debug=False):
        self._debug = debug
        self._duration = duration
        self._iterations = iterations
        self._turbostat = TurboStat(duration)
        self._powertop = PowerTop(duration)

    def _collect_power_usage(self):
        df = DataFrame(columns=fields)

        for i in range(0, self._iterations):
            if self._debug:
                print("Starting run", i)
            df = self._run_iteration(df)

        return df.convert_objects(convert_numeric=True)

    def _run_iteration(self, df):
        self.initialize_iteration()

        self._turbostat.start()
        self.execute_iteration()
        summary = self._turbostat.join()

        # run powertop
        self._powertop.start()
        wakeups = self._powertop.join()
        summary["wakeups"] = wakeups

        self.finalize_iteration()
        return df.append(summary, ignore_index=True)

    def log(self, filename=None):
        self.initialize()
        df = self._collect_power_usage()
        df.describe().to_csv(filename) if filename else None
        self.process_measurements(df)
        self.finalize()

    def initialize(self):
        pass

    def initialize_iteration(self):
        pass

    def execute_iteration(self):
        pass

    def finalize_iteration(self):
        pass

    def process_measurements(self, df):
        pass

    def finalize(self):
        pass

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Collect power usage statistics.",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=5, type=int)
    parser.add_argument("-o", "--output", help="Path of the csv output", default="report.csv")
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    summary = PowerSummary(args.duration, args.iterations, args.debug)
    summary.log(args.output)
