import scipy
import scipy.fftpack
import scipy.stats
import pylab
import argparse
import datetime
import time
import numpy
import os
import platform
import re
import shutil
import sys
import uuid
import tempfile
import functools
import multiprocessing

from bisect import bisect_left
from datetime import datetime, timedelta

def binary_search(a, x, lo=0, hi=None):
    hi = hi if hi is not None else len(a)
    pos = bisect_left(a,x,lo,hi)
    return (pos if pos != hi and a[pos] == x else -1)

class PowerGadget:
    _osx_exec = "PowerLog"
    _win_exec = "PowerLog.exe"
    _lin_exec = "power_gadget"

    def __init__(self, path):
        self._system = platform.system()

        if path:
            if os.path.exists(path):
                self._path = path
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Darwin":
            if shutil.which(PowerGadget._osx_exec):
                self._path = PowerGadget._osx_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Linux":
            if shutil.which(PowerGadget._lin_exec):
                self._path = PowerGadget._lin_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Windows":
            if shutil.which(PowerGadget._win_exec):
                self._path = PowerGadget._win_exec
            else:
                raise Exception("Intel Power Gadget executable not found")
        else:
            raise Exception("Platform is not supported.")

    def _start(self, resolution, duration, filename):
        if self._system == "Darwin":
            os.system(self._path +  " -resolution " + str(resolution) + " -duration " +
                      str(duration) + " -file " + filename + " > /dev/null")
        elif self._system == "Linux":
            os.system(self._path +  " -e " + str(resolution) + " -d " +
                      str(duration) + " > " + filename)
        else:
            os.system(self._path +  " -resolution " + str(resolution) + " -duration " +
                      str(duration) + " -file " + filename)

    def start(self, resolution, duration, filename):
        self._log_process = multiprocessing.Process(target=functools.partial(self._start, resolution, duration, filename))
        self._log_process.start()

    def join(self):
        assert(self._log_process)
        self._log_process.join()

class Signal:
    def __init__(self, sequence, timestamps, cumulative_joules, frequency, duration):
        self._sequence = sequence
        self._timestamps = timestamps
        self._cumulative_joules = cumulative_joules
        self._frequency = frequency
        self._duration = duration
        self._start_time = timestamps[0]
        self._end_time = timestamps[0] + timedelta(0, duration)
        self._aticks = []
        self._alabels = []

    def get_joules(self, start_ts=None, end_ts=None):
        start = 0
        end = len(self._cumulative_joules) - 1

        if start_ts:
            start = bisect_left(self._timestamps, start_ts)
            assert(start <= self._end_time)
            assert(start >= self._start_time)

        if end_ts:
            end = bisect_left(self._timestamps, end_ts)
            assert(end <= self._end_time)
            assert(end >= self._start_time)

        start = self._cumulative_joules[start]
        end = self._cumulative_joules[end]
        return end - start

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_length(self):
        return len(self._sequence)

    def annotate(self, annotations):
        if not annotations:
            return

        for ts, label in annotations:
            if ts < self._start_time or ts > self._end_time:
                continue

            self._aticks.append((ts -self._start_time).total_seconds()/self._duration)
            self._alabels.append(label)

    def plot(self, filename, title="", show=False):
        length = self.get_length()
        t = scipy.linspace(0, self._duration, len(self._sequence))
        fft = abs(scipy.fft(self._sequence))
        f = scipy.linspace(0, self._frequency/2.0, length/2.0)

        pylab.suptitle(title)
        pylab.subplots_adjust(hspace=0.5, top=0.8)
        ax1 = pylab.subplot(211)
        pylab.plot(t, self._sequence)
        pylab.ylabel("Watt")
        pylab.xlabel("time (sec)")
        ax2 = ax1.twiny()
        ax2.set_xticks(self._aticks)
        ax2.set_xticklabels(self._alabels, rotation="vertical")

        pylab.subplot(212)
        #don't plot the mean
        pylab.plot(f[1:], 2.0/length*abs(fft[1:length//2]))
        pylab.ylabel('amplitude')
        pylab.xlabel('frequency (hz)')
        pylab.savefig(filename)

        if show:
            pylab.show()
        pylab.clf()

    @staticmethod
    def parse(path, frequency, duration, start_time, debug=False):
        signal = []
        cumulative_joules = []
        timestamps = []

        with open(path) as f:
            lines = f.readlines()
            data = []
            metadata = []

            # split in data and metadata
            for iteration, line in enumerate(lines):
                if line == "\n":
                    data = lines[1:iteration]
                    metadata = lines[iteration + 1:]
                    break

            # print metadata if required
            for line in metadata:
                line = line.strip()
                if line and debug:
                    print(line)

            # assume duration < 24h
            one_day = timedelta(1)
            assert(duration < (24*60*60 - 60))

            for line in data:
                fields = line.split(",")

                ts = datetime.strptime("{}:{}:{} {}".format(start_time.month, start_time.day, start_time.year, fields[0]), "%m:%d:%Y %H:%M:%S:%f")
                if ts < start_time:
                    ts = ts + one_day

                timestamps.append(ts)
                signal.append(float(fields[4]))
                cumulative_joules.append(float(fields[5]))

        assert(len(signal) > 0)

        return Signal(signal, timestamps, cumulative_joules, frequency, duration)

class PowerLogger:
    def __init__(self, gadget_path="", debug=False):
        self._powergadget = PowerGadget(gadget_path)
        self._debug = debug
        self._annotations = []

    def _create_tmp_dir(self):
        directory = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))

        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

        return directory

    def _remove_tmp_dir(self, directory):
        if self._debug:
            print("Logs saved to:", directory)
        else:
            shutil.rmtree(directory)

    def _collect_power_usage(self, directory, resolution, frequency, duration, iterations):
        signals = []

        for i in range(0, iterations):
            if self._debug:
                print("Starting run", i)

            report = os.path.join(directory, "log_" + str(i))
            signals.append(self._run_iteration(resolution, frequency, duration, report))

        return signals

    def _predict_duration(self):
        self.initialize_iteration()
        start = datetime.now()
        self.execute_iteration()
        end = datetime.now()
        self.finalize_iteration()
        return int((end - start).total_seconds()) + 5 #magic number

    def _run_iteration(self, resolution, frequency, duration, report):
        # Decorate power usage logging with template methods
        self._annotations = []
        self.initialize_iteration()

        start_time = datetime.now()
        self._powergadget.start(resolution, duration, report + ".log")
        self.execute_iteration()
        end_time = datetime.now()

        self._powergadget.join()
        self.finalize_iteration()

        signal = Signal.parse(report + ".log", frequency, duration, start_time, self._debug)
        signal.annotate(self._annotations)

        assert(end_time < signal.get_end_time())

        if self._debug:
            signal.plot(report + ".png")

        return signal

    def _mean_confidence_interval(self, signals, confidence=0.95):
        data = [signal.get_joules() for signal in signals]
        mean = numpy.mean(data)
        se = scipy.stats.sem(data)
        n = len(data)
        h = se * scipy.stats.t.ppf((1 + confidence)/2., n - 1)
        return mean, h

    def _show_closest_signal(self, directory, signals, freq, duration, mean, range):
        min = lambda x, y: x if abs(x.get_joules() - mean) < abs(y.get_joules() - mean) else y
        signal = functools.reduce(min, signals)
        title = "Mean of {:.2f} += {:.2f} Joules for {} runs of {} s at {:.2f} hz".\
                 format(mean, range, len(signals), duration, freq)
        signal.plot(os.path.join(directory, "report.png"), title, True)

    def log(self, resolution, iterations, duration=None):
        directory = self._create_tmp_dir()
        frequency = 1000.0/resolution

        #run prediction in any case as a warm up run
        predicted_duration = self._predict_duration()
        duration = duration if duration else predicted_duration

        signals = self._collect_power_usage(directory, resolution, frequency, duration, iterations)
        m, r = self._mean_confidence_interval(signals)
        self._show_closest_signal(directory, signals, frequency, duration, m, r)
        self._remove_tmp_dir(directory)

    def add_marker(self, message):
        self._annotations.append((datetime.now(), message))

    def initialize_iteration(self):
        pass

    def execute_iteration(self):
        pass

    def finalize_iteration(self):
        pass


if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Plot Power Gadget's logs in time and frequency domain",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms", default=50, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=60, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=2, type=int)
    parser.add_argument("-p", "--gadget_path", help="Intel's Power Gadget path", default="")
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    logger = PowerLogger(args.gadget_path, args.debug)
    logger.log(args.resolution, args.iterations, args.duration)
