import os
import platform
import rpy2.robjects as ro
import rpy2.robjects.lib.ggplot2 as ggplot2

from power_logger import PowerLogger
from subprocess import Popen
from time import sleep
from rpy2.robjects.packages import importr

gridExtra = importr("gridExtra")
grDevices = importr('grDevices')

measurements = {"Browser":[], "Page":[], "Joules":[], "CI":[], "Runs":[], "sec":[], "hz":[], "signal":[]}

class IdleLogger(PowerLogger):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    # This method is run before all iterations
    def initialize(self):
        self.browser.initialize()
        #sleep(100)
        pass

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        pass

    def process_measurements(self, m, r, signals, closest_signal, duration, frequency):
        measurements["Browser"].append(self.browser.get_name())
        measurements["Page"].append(self.browser.get_page())
        measurements["Joules"].append(m)
        measurements["CI"].append(r)
        measurements["Runs"].append(len(signals))
        measurements["sec"].append(duration)
        measurements["hz"].append(frequency)
        measurements["signal"].append(closest_signal)

    # This method is run after all iterations
    def finalize(self):
        self.browser.finalize()
        #sleep(5)
        sleep(1)
        pass

class WinBrowser:
    def __init__(self, browser, page):
        self.page = page

        if browser == "firefox":
            self.browser = "firefox"
            self.description = "Firefox"
        elif browser == "chrome":
            self.browser = "chrome"
            self.description = "Chrome"
        elif browser == "ie":
            self.browser = "iexplore"
            self.description = "Internet Explorer"
        else:
            assert(0)

    def initialize(self):
        # We can't use Popen... terminate() doesn't shutdown the FF properly among all OSs
        os.system("start " + self.browser + " " + self.page)
        pass

    def finalize(self):
        os.system("taskkill /im " + self.browser + ".exe > NUL 2>&1")
        pass

    def __str__(self):
        return 'Win, ' + self.description + ', ' + self.page

class OSXBrowser:
    def __init__(self, browser, page):
        self.page = page

        if browser == "firefox":
            self.browser = "Firefox.app"
            self.description = "Firefox"
        elif browser =="firefox-nightly":
            self.browser = "FirefoxNightly.app"
            self.description = "Firefox Nightly"
        elif browser == "chrome":
            self.browser = "Google Chrome.app"
            self.description = "Chrome"
        elif browser == "safari":
            self.browser = "Safari.app"
            self.description = "Safari"
        else:
            assert(0)

    def initialize(self):
        if self.browser == "Safari.app":
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " " + "http://" + self.page)
        else:
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " --args " + self.page)

    def finalize(self):
        os.system('osascript -e \"tell application \\\"' + self.browser + '\\\" to quit\"')

    def get_OS(self):
        return "OSX"

    def get_name(self):
        return self.description

    def get_page(self):
        return self.page

    def __str__(self):
        return 'OSX, ' + self.description + ', ' + self.page

class UbuntuBrowser:
    def __init__(self, browser, page):
        self.page = page

        if browser == "firefox":
            self.browser = "firefox"
            self.description = "Firefox"
        elif browser == "firefox-nightly":
            self.browser = "firefox-trunk"
            self.description = "Firefox"
        elif browser == "chrome":
            self.browser = "chromium-browser"
            self.description = "Chromium"
        else:
            raise

    def initialize(self):
        os.system(self.browser + " " + self.page + " > /dev/null 2>&1 &")

    def finalize(self):
        if self.browser == "chromium-browser":
            os.system("wmctrl -c Chromium")
        else:
            os.system("wmctrl -c " + self.browser)

    def __str__(self):
        return 'Ubuntu, ' + self.description + ', ' + self.page

def BrowserFactory(browser, page):
    if platform.system() == "Linux":
        return UbuntuBrowser(browser, page)
    elif platform.system() == "Darwin":
        return OSXBrowser(browser, page)
    elif platform.system() == "Windows":
        return WinBrowser(browser, page)
    else:
        assert(0)

websites = ["about:blank", "www.youtube.com", "www.yahoo.com",
            "www.amazon.com", "www.ebay.com", "www.google.com",
            "www.facebook.com", "www.wikipedia.com", "www.craigslist.com"]

if __name__ == "__main__":
    for page in websites[:1]:
        #for browser in ["firefox", "chrome", "safari", "ie"]:
        for browser in ["chrome", "safari", "ie"]:
            try:
                browser = BrowserFactory(browser, page)
                logger = IdleLogger(browser)
                #logger.log(resolution=50, iterations=10, duration=30, plot=False)
                logger.log(resolution=50, iterations=2, duration=1, plot=False)
            except:
                pass

    frame = ro.DataFrame({"Browser": ro.StrVector(measurements["Browser"]),
        "Page": ro.StrVector(measurements["Page"]),
        "Joules": ro.FloatVector(measurements["Joules"]),
        "CI": ro.FloatVector(measurements["CI"])})

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
    for i in range(0, len(measurements["signal"])):
        title = measurements["Browser"][i] + " " + measurements["Page"][i]
        plots.append(measurements["signal"][i].get_time_freq_plots()[0] + ggplot2.ggtitle(title))

    gridExtra.grid_arrange(*plots)
    sleep(5)
