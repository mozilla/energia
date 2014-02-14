import os
import platform
import argparse
import json

from power_logger import PowerLogger
from subprocess import Popen
from time import sleep

_plotting_enabled = False
_measurements = {"Browser":[], "Page":[], "Watts":[], "CI":[], "Runs":[], "sec":[], "hz":[], "signal":[]}
_config = None
_args = None

try:
    #Use Rpy2 & ggplot2 only if plotting is required
    import rpy2.robjects as ro
    import rpy2.robjects.lib.ggplot2 as ggplot2
    from rpy2.robjects.packages import importr
    gridExtra = importr("gridExtra")
    grDevices = importr('grDevices')
    _plotting_enabled = True
except:
    pass

class IdleLogger(PowerLogger):
    def __init__(self, browser, gadget_path):
        super().__init__(gadget_path=gadget_path)
        self.browser = browser

    # This method is run before all iterations
    def initialize(self):
        self.browser.initialize()
        sleep(_args.sleep)

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        pass

    def process_measurements(self, m, r, signals, closest_signal, duration, frequency):
        _measurements["Browser"].append(self.browser.get_name())
        _measurements["Page"].append(self.browser.get_page())
        _measurements["Watts"].append(m)
        _measurements["CI"].append(r)
        _measurements["Runs"].append(len(signals))
        _measurements["sec"].append(duration)
        _measurements["hz"].append(frequency)
        _measurements["signal"].append(closest_signal)

    # This method is run after all iterations
    def finalize(self):
        self.browser.finalize()
        sleep(5)

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
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " " + ("http://" if not self.page.startswith("http") else "") + self.page)
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
        elif self.browser == "firefox-trunk":
            os.system("wmctrl -c Nightly")
        else:
            os.system("wmctrl -c " + self.browser)

def get_pages():
    return _config["Pages"]

def get_browsers():
    os = platform.system()
    return _config["OS"][os]

def run_benchmark():
    for page in get_pages():
        for b in get_browsers():
            browser = Browser.create_browser(name=b["name"], path=b["path"], page=page)
            logger = IdleLogger(browser, _args.gadget_path)
            logger.log(resolution=_args.resolution, iterations=_args.iterations, duration=_args.duration)

def plot_data(width=1024, height=300):
    if not _plotting_enabled:
        print("Warning: plotting requested but disabled due to unmet dependencies (rpy2 & ggplot2)")
        return

    frame = ro.DataFrame({"Browser": ro.StrVector(_measurements["Browser"]),
        "Page": ro.StrVector(_measurements["Page"]),
        "Watts": ro.FloatVector(_measurements["Watts"]),
        "CI": ro.FloatVector(_measurements["CI"])})

    title = "Idle power measurements for {} runs of {}s each at {}hz on {}".format(
               _args.iterations, _args.duration, 1000.0/_args.resolution, platform.system())

    p = ggplot2.ggplot(frame) + \
           ggplot2.aes_string(x="Page", y="Watts", fill="Browser") + \
           ggplot2.geom_bar(position="dodge", stat="identity") + \
           ggplot2.geom_errorbar(ggplot2.aes_string(ymax="Watts+CI", ymin="Watts-CI"),
                                 position=ggplot2.position_dodge(0.9), width=0.4) + \
           ggplot2.theme(**{'plot.title': ggplot2.element_text(size = 13)}) + \
           ggplot2.theme_bw() + ggplot2.ggtitle(title)

    plots = [p]
    n_browsers = len(get_browsers())
    n_pages = len(get_pages())

    for i in range(0, n_pages):
        tmp_plots = []

        # get highest usage
        scale = 0
        for j in range(0, n_browsers):
            index = i*n_browsers + j
            scale = max(_measurements["signal"][index].get_max_watts(), scale)

        for j in range(0, n_browsers):
            index = i*n_browsers + j
            title = _measurements["Browser"][index] + " " + _measurements["Page"][index]
            wplot = _measurements["signal"][index].get_time_freq_plots()[0] + \
                    ggplot2.ggtitle(title) + \
                    ggplot2.scale_y_continuous(limits=ro.IntVector([0, scale+1]))
            tmp_plots.append(wplot)

        plots.append(gridExtra.arrangeGrob(*tmp_plots, ncol=n_browsers))

    grDevices.png(file=_args.png_output, width=width, height=height * len(plots))
    gridExtra.grid_arrange(gridExtra.arrangeGrob(*plots, nrow=n_pages + 1))
    grDevices.dev_off()

def dump_csv():
    m = _measurements

    with open(_args.csv_output, 'w') as f:
        f.write("OS, Browser, Page, Watts, CI, Runs, Sec, Hz\n")
        for i in range(len(m["Browser"])):
            f.write("{}, {}, {}, {:.2f}, {:.2f}, {}, {}, {:.2f}\n".format(platform.system(),
                m["Browser"][i], m["Page"][i], m["Watts"][i], m["CI"][i], m["Runs"][i],
                m["sec"][i], m["hz"][i]))

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Idle power benchmark",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--png_output", help="Path of the final .png plot", default="report.png")
    parser.add_argument("-t", "--csv_output", help="Path of the emitted csv file", default="report.csv")
    parser.add_argument("-c", "--config", help="Configuration file", default="config.json")
    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms", default=50, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=10, type=int)
    parser.add_argument("-s", "--sleep", help="Seconds to sleep before the benchmark starts recording the power usage", default=100, type=int)
    parser.add_argument("-p", "--gadget_path", help="Intel's Power Gadget path", default="")
    _args = parser.parse_args()

    with open(_args.config) as f:
        _config = json.load(f)

    run_benchmark()
    dump_csv()
    plot_data()
