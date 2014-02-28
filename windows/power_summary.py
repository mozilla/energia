import argparse
import tempfile
import os
import uuid
import shutil
import re
import pandas

from subprocess import Popen, PIPE
from pandas import DataFrame

fields = ["CPU % (Platform)", "CPU % (Logical)", "CPU Proc % (Platform)", "CPU Proc % (Logical)", "Idle Wakeups", "Idle Proc Wakeups"]

class BLA:
    def __init__(self, duration=5, image=None):
        self._process = None
        self._duration = duration
        self._directory = "tmp"
        self._image = None

        if image:
            self._image = image if image.endswith(".exe") else image + ".exe"

    def start(self):
        # Can't use tempfile bc BLA doesn't support abbreviated filenames
        self._process = Popen('BLA.exe c sw:{} -o {}'.format(self._duration, self._directory))
        pass

    def join(self):
        self._process.wait()
        path = os.path.join(self._directory, "Active Analysis.csv")
        aa_df = pandas.io.parsers.read_csv(path, sep="\t", encoding="utf-16")

        entry = {}
        entry["CPU % (Platform)"] = aa_df['CPU % (Platform)'][0]
        entry["CPU % (Logical)"] = aa_df['CPU % (Logical)'][0]
        entry["Idle Wakeups"] = aa_df['CSwitches from Idle'][0]
        print(aa_df['CPU % (Platform)'][0])

        if self._image != None:
            selection = aa_df[aa_df['Image Name'] == self._image]
            if len(selection > 0):
                entry["CPU Proc % (Platform)"] = selection["CPU % (Platform)"].sum()
                entry["CPU Proc % (Logical)"] = selection["CPU % (Logical)"].sum()
                entry["Idle Proc Wakeups"] = selection["CSwitches from Idle"].sum()

        #shutil.rmtree(self._directory)
        return entry

class PowerSummary:
    def __init__(self, duration, iterations, image=None, debug=False):
        self._debug = debug
        self._duration = duration
        self._iterations = iterations
        self._bla = BLA(duration, image)

    def _collect_power_usage(self):
        df = DataFrame(columns=fields)

        for i in range(0, self._iterations):
            if self._debug:
                print("Starting run", i)
            df = self._run_iteration(df)

        return df.convert_objects(convert_numeric=True)

    def _run_iteration(self, df):
        self.initialize_iteration()

        self._bla.start()
        self.execute_iteration()
        summary = self._bla.join()
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
    parser.add_argument("-p", "--process", help="Name of the process to monitor", default=None)
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    summary = PowerSummary(args.duration, args.iterations, args.process, args.debug)
    summary.log(args.output)
