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

from datetime import datetime
from scipy import pi

class PowerGadget:
    def __init__(self, path):
        self._system = platform.system()

        if path:
            if os.path.exists(path):
                self._path = path
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Darwin":
            if shutil.which("PowerLog"):
                self._path = "PowerLog"
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Linux":
            if(shutil.which("power_gadget")):
                self._path = "power_gadget"
            else:
                raise Exception("Intel Power Gadget executable not found")
        elif self._system == "Windows":
            if(shutil.which("PowerLog")):
                self._path = "PowerLog"
            else:
                raise Exception("Intel Power Gadget executable not found")
        else:
            raise Exception("Platform is not supported.")

    def get_temporary_path(self):
        if self._system == "Darwin" or self._system == "Linux":
            return "/tmp/"
        else:
            return ""

    def log(self, resolution, duration, filename):
        if self._system == "Darwin":
            os.system(self._path +  " -resolution " + str(resolution) + " -duration " +
                      str(duration) + " -file " + filename + " > /dev/null")
        elif self._system == "Linux":
            os.system(self._path +  " -e " + str(resolution) + " -d " +
                      str(duration) + " > " + filename)
        else:
            raise Exception("Platform is not supported")

def plot_signal(signal, sampling_frequency, interval, filename, title, show=False):
    sample_time = 1.0/sampling_frequency;
    t = scipy.linspace(0, interval, len(signal))
    fft = abs(scipy.fft(signal))
    f = scipy.linspace(0, sampling_frequency/2.0, len(signal)/2.0)

    pylab.suptitle(title)
    pylab.subplot(211)
    pylab.title("Sample run")
    pylab.plot(t, signal)
    pylab.ylabel("Watt")
    pylab.xlabel("time (sec)")

    pylab.subplot(212)
    #don't plot the mean
    pylab.plot(f[1:], 2.0/len(signal)*abs(fft[1:len(signal)//2]))
    pylab.ylabel('amplitude')
    pylab.xlabel('frequency (hz)')
    pylab.savefig(filename)
    if show:
        pylab.show()
    pylab.clf()

def parse_signal(path, debug):
    signal = []
    joules = 0

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

        # parse metadata
        regexp = re.compile('.*Processor Energy_0\s?\(Joules\)\s?=\s?(.*)')
        for line in metadata:
            line = line.strip()

            m = regexp.match(line)
            if m:
                joules = float(m.group(1))

            if line and debug:
                print(line)

        # remove the first and last line which might have zero values
        data = data[1:-1]

        fields1 = data[1].split(",")
        fields2 = data[2].split(",")
        ts = (abs(int(fields1[0].split(":")[-1]) - int(fields2[0].split(":")[-1]))//10)*10

        freq = int(1000.0/ts);

        for line in data:
            fields = line.split(",")
            signal.append(float(fields[4]))

    assert(joules > 0)
    assert(len(signal) > 0)

    return (signal, freq, joules)

def collect_power_usage(powerlog, directory, resolution, duration, iterations, debug):
    joules = iterations * [None]
    signals = iterations * [None]

    for i in range(0, iterations):
        if debug:
            print("Starting run", i)

        report = os.path.join(directory, "log_" + str(i))
        powerlog.log(resolution, duration, report + ".log")
        signals[i], freq, joules[i] = parse_signal(report + ".log", debug)

        if debug:
            plot_signal(signals[i], freq, duration, report + ".png", "Run " + str(i))

    return signals, joules

def mean_confidence_interval(data, confidence=0.95):
    mean = numpy.mean(data)
    se = scipy.stats.sem(data)
    n = len(data)
    h = se * scipy.stats.t.ppf((1 + confidence)/2., n - 1)
    return mean, h

def display_nearest_plot(directory, signals, joules, freq, duration, mean, range):
    min_dist = abs(joules[0] - mean)
    min_elem = 0

    for index, joule in enumerate(joules):
        dist = abs(joule - mean)
        if dist < min_dist:
            min_dist = dist
            min_elem = index;

    title = "Mean of {:.2f} += {:.2f} Joules for {} runs of {} s at {:.2f} hz".\
             format(mean, range, len(signals), duration, freq)
    plot_signal(signals[min_elem], freq, duration, os.path.join(directory, "report.png"), title, True)

def main():
    parser= argparse.ArgumentParser(description="Plot Power Gadget's logs in time and frequency domain",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms", default=75, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=60, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=2, type=int)
    parser.add_argument("-p", "--gadget_path", help="Intel's Power Gadget path", default="")
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    if(args.iterations <= 1):
        raise Exception("iterations has to be greater than 1")
    if(args.duration <= 0):
        raise Exception("duration has to be greater than 0")
    if(args.resolution < 50):
        raise Exception("resolution has to be greater or equal to 50")

    powergadget = PowerGadget(args.gadget_path)
    # use tmpfs on Linux to avoid periodic disk writes (doesn't happen on OSX and Windows)
    directory = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    frequency = 1000.0/args.resolution

    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

    signals, joules = collect_power_usage(powergadget, directory, args.resolution, args.duration, args.iterations, args.debug)
    m, r = mean_confidence_interval(joules)
    display_nearest_plot(directory, signals, joules, frequency, args.duration, m, r)

    if args.debug:
        print("Logs saved to:", directory)
    else:
        shutil.rmtree(directory)


if __name__ == "__main__":
    main()
