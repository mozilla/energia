import pandas
import sys
import os
import shutil

sys.path.append("..")

from wrapper import Wrapper
from pandas import DataFrame
from subprocess import Popen, PIPE

class BLA(Wrapper):
    def __init__(self, args):
        super().__init__(args)
        self._process = None
        self._directory = "tmp"
        self._image = args.image if args.image else None
        self._fields = ["CPU % (Platform)", "CPU % (Logical)", "CPU Proc % (Platform)",
                        "CPU Proc % (Logical)", "Idle Wakeups", "Idle Proc Wakeups",
                        "Power Impact", "Power Proc Impact"]

        if self._image:
            self._image = self._image if self._image.endswith(".exe") else self._image + ".exe"

    def start(self):
        # Can't use tempfile bc BLA doesn't support abbreviated filenames
        self._process = Popen('BLA.exe c sw:{} -o {}'.format(self._args.duration, self._directory))

    def join(self):
        self._process.wait()
        path = os.path.join(self._directory, "Active Analysis.csv")
        aa_df = pandas.io.parsers.read_csv(path, sep="\t", encoding="utf-16")

        entry = {}
        entry["CPU % (Platform)"] = aa_df['CPU % (Platform)'][0]
        entry["CPU % (Logical)"] = aa_df['CPU % (Logical)'][0]
        entry["Idle Wakeups"] = aa_df['CSwitches from Idle'][0]
        entry["Power Impact"] = aa_df['Power Impact (W) - HuronRiver - Sandybridge - Dual Core'][0]
        print(aa_df['CPU % (Platform)'][0])

        if self._image != None:
            selection = aa_df[aa_df['Image Name'] == self._image]
            if len(selection > 0):
                entry["CPU Proc % (Platform)"] = selection["CPU % (Platform)"].sum()
                entry["CPU Proc % (Logical)"] = selection["CPU % (Logical)"].sum()
                entry["Idle Proc Wakeups"] = selection["CSwitches from Idle"].sum()
                entry["Power Proc Impact"] = selection['Power Impact (W) - HuronRiver - Sandybridge - Dual Core'].sum()

        shutil.rmtree(self._directory)
        return entry
