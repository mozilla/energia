import sys
import platform
import shutil
import os
import multiprocessing
import pandas
import re

sys.path.append("..")

from wrapper import Wrapper
from pandas import DataFrame

class PowerGadget(Wrapper):
    _osx_exec = "PowerLog"
    _win_exec = "PowerLog.exe"
    _lin_exec = "power_gadget"

    def __init__(self, args):
        super().__init__(args)

        self._fields = ["Joules", "Watt"]
        self._system = platform.system()

        directory = "tmp"
        self._logfile = os.path.join(directory, "PowerLog.ipg")

        if not os.path.exists(directory):
            os.makedirs(directory)

        if self._args.path:
            if os.path.exists(self._args.path) and os.access(self._args.path, os.X_OK):
                self._log = self._args.path
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Darwin":
            if shutil.which(PowerGadget._osx_exec):
                self._log = PowerGadget._osx_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Linux":
            if shutil.which(PowerGadget._lin_exec):
                self._log = PowerGadget._lin_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Windows":
            if shutil.which(PowerGadget._win_exec):
                self._log = PowerGadget._win_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        else:
            raise Exception("Platform is not supported.")

    def __del__(self):
        shutil.rmtree(os.path.split(self._logfile)[0])

    def start(self):
        self._log_process = multiprocessing.Process(target=self._start)
        self._log_process.start()

    def _start(self):
        resolution = self._args.resolution
        duration = self._args.duration

        if self._system == "Darwin":
            os.system("{} -resolution {} -duration {} -file {} > /dev/null".format(
                      self._log, str(resolution), str(duration), self._logfile))
        elif self._system == "Linux":
            os.system("{} -e {} -d {} > {}".format(self._log, str(resolution),
                      str(duration), self._logfile))
        else:
            os.system("{} -resolution {} -duration {} -file {} > NUL 2>&1".format(
                      self._log, str(resolution), str(duration), self._logfile))

    def join(self):
        self._log_process.join()
        res = self._parse()
        return res

    def _parse(self):
        joules = 0
        watts = 0
        joules_re = re.compile(".*\(Joules\) = (.*)")
        watt_re = re.compile(".*\(Watt\) = (.*)")

        try:
            with open(self._logfile) as f:
                lines = f.readlines()

                # split in data and metadata
                for iteration, line in enumerate(lines):
                    if line == "\n":
                        data = lines[:iteration]
                        metadata = lines[iteration + 1:]
                        break

                for line in metadata:
                    m = re.match(joules_re, line)
                    if m:
                        joules = float(m.group(1))

                    m = re.match(watt_re, line)
                    if m:
                        watt = float(m.group(1))

        except FileNotFoundError:
            raise Exception("PowerLog failed to generate a valid logfile")
            return sys.exit(-1)

        assert(watt > 0 and joules > 0)
        return {"Watt" : watt, "Joules": joules}
