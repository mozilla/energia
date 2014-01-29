import os
import platform
import rpy2.robjects as ro
import rpy2.robjects.lib.ggplot2 as ggplot2
import argparse
import json

from power_logger import PowerLogger
from subprocess import Popen
from time import sleep
from rpy2.robjects.packages import importr

_measurements = {"Browser":[], "Page":[], "Joules":[], "CI":[], "Runs":[], "sec":[], "hz":[], "signal":[]}
_config = None

class IdleLogger(PowerLogger):
    def __init__(self, browser, gadget_path):
        super().__init__(gadget_path=gadget_path)
        self.browser = browser

    # This method is run before all iterations
    def initialize(self):
        self.browser.initialize()
        sleep(100)
        pass

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        pass

    def process_measurements(self, m, r, signals, closest_signal, duration, frequency):
        _measurements["Browser"].append(self.browser.get_name())
        _measurements["Page"].append(self.browser.get_page())
        _measurements["Joules"].append(m)
        _measurements["CI"].append(r)
        _measurements["Runs"].append(len(signals))
        _measurements["sec"].append(duration)
        _measurements["hz"].append(frequency)
        _measurements["signal"].append(closest_signal)

    # This method is run after all iterations
    def finalize(self):
        self.browser.finalize()
        sleep(5)
        pass

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
        elif os == "Darwin":
            return OSXBrowser(name, path, page)
        elif os == "Windows":
            return WinBrowser(name, path, page)
        else:
            assert(0)

class WinBrowser(Browser):
    def __init__(self, name, path, page):
        super().__init__(name, path, page)

    def initialize(self):
        # We can't use Popen... terminate() doesn't shutdown the FF properly among all OSs
        os.system("start " + self.browser + " " + self.page)

    def finalize(self):
        os.system("taskkill /im " + self.browser + ".exe")

class OSXBrowser(Browser):
    def __init__(self, name, path, page):
        super().__init__(name, path, page)

    def initialize(self):
        if self.description == "Safari":
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " " + "http://" + self.page)
        else:
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " --args " + self.page)

    def finalize(self):
        os.system('osascript -e \"tell application \\\"' + self.browser + '\\\" to quit\"')

class UbuntuBrowser(Browser):
    def __init__(self, name, path, page):
        super().__init__(name, path, page)

    def initialize(self):
        os.system(self.browser + " " + self.page + "&")

    def finalize(self):
        if self.browser == "chromium-browser":
            os.system("wmctrl -c Chromium")
        else:
            os.system("wmctrl -c " + self.browser)

def get_pages():
    return _config["Pages"]

def get_browsers():
    os = platform.system()
    return _config["OS"][os]

def run_benchmark(args):
    for page in get_pages():
        for b in get_browsers():
            browser = Browser.create_browser(name=b["name"], path=b["path"], page=page)
            logger = IdleLogger(browser, args.gadget_path)
            logger.log(resolution=args.resolution, iterations=args.iterations, duration=args.duration, plot=False)

def plot_data(filename, width=1024, height=300):
    gridExtra = importr("gridExtra")
    grDevices = importr('grDevices')

    frame = ro.DataFrame({"Browser": ro.StrVector(_measurements["Browser"]),
        "Page": ro.StrVector(_measurements["Page"]),
        "Joules": ro.FloatVector(_measurements["Joules"]),
        "CI": ro.FloatVector(_measurements["CI"])})

    p = ggplot2.ggplot(frame) + \
           ggplot2.aes_string(x="Page", y="Joules", fill="Browser") + \
           ggplot2.geom_bar(position="dodge", stat="identity") + \
           ggplot2.geom_errorbar(ggplot2.aes_string(ymax="Joules+CI", ymin="Joules-CI"),
                                 position=ggplot2.position_dodge(0.9), width=0.4) + \
           ggplot2.theme(**{'plot.title': ggplot2.element_text(size = 13)}) + \
           ggplot2.theme_bw() + \
           ggplot2.ggtitle("Idle power measurements for {} runs of {}s each at {}hz on {}".format(
               2, 1, 1000.0/50, "OSX"))

    plots = [p]
    n_browsers = len(get_browsers())
    n_pages = len(get_pages())

    for i in range(0, n_pages):
        tmp_plots = []

        for j in range(0, n_browsers):
            index = i*n_browsers + j
            title = _measurements["Browser"][index] + " " + _measurements["Page"][index]
            tmp_plots.append(_measurements["signal"][index].get_time_freq_plots()[0] + ggplot2.ggtitle(title))

        plots.append(gridExtra.arrangeGrob(*tmp_plots, ncol=n_browsers))

    grDevices.png(file=filename, width=width, height=height * len(plots))
    gridExtra.grid_arrange(gridExtra.arrangeGrob(*plots, nrow=n_pages + 1))
    grDevices.dev_off()

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Idle power benchmark",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--output", help="Path of the final .png plot", default="report.png")
    parser.add_argument("-c", "--config", help="Configuration file", default="idle_config.json")
    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms", default=50, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=10, type=int)
    parser.add_argument("-p", "--gadget_path", help="Intel's Power Gadget path", default="")
    args = parser.parse_args()

    with open(args.config) as f:
        _config = json.load(f)

    run_benchmark(args)
    plot_data(args.output)
