from power_logger import PowerLogger
from subprocess import Popen
from time import sleep
import os
import platform

class IdleLogger(PowerLogger):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    # This method is run before all iterations
    def initialize(self):
        self.browser.initialize()
        sleep(100)
        pass

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        pass

    def process_measurements(self, m, r, signals, duration, frequency):
        print("{} - mean of {:.2f} += {:.2f} Joules for {} runs of {} s at {:.2f} hz".\
              format(self.browser, m, r, len(signals), duration, frequency))

    # This method is run after all iterations
    def finalize(self):
        self.browser.finalize()
        sleep(5)
        pass

class OSXBrowser:
    def __init__(self, browser, page):
        self.page = page

        if browser == "firefox":
            self.browser = "Firefox.app"
        elif browser =="firefox-nightly":
            self.browser = "FirefoxNightly.app"
        elif browser == "chrome":
            self.browser = "Google Chrome.app"
        elif browser == "safari":
            self.browser = "Safari.app"
        else:
            assert(0)

    def initialize(self):
        # We can't use Popen... terminate() doesn't shutdown the FF properly among all OSs
        if self.browser == "Safari.app":
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " " + "http://" + self.page)
        else:
            os.system("open -a " + self.browser.replace(" ", "\\ ") + " --args " + self.page)

    def finalize(self):
        os.system('osascript -e \"tell application \\\"' + self.browser + '\\\" to quit\"')

    def __str__(self):
        return 'OSX, ' + self.browser + ', ' + self.page

class UbuntuBrowser:
    def __init__(self, browser, page):
        self.page = page

        if browser == "firefox":
            self.browser = "firefox"
        elif browser == "firefox-nightly":
            self.browser = "firefox-trunk"
        elif browser == "chrome":
            self.browser = "chromium-browser"
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
        return 'Ubuntu, ' + self.browser + ', ' + self.page

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

for page in websites[:]:
    for browser in ["firefox", "chrome", "safari"]:
        try:
            browser = BrowserFactory(browser, page)
            logger = IdleLogger(browser)
            logger.log(50, 10, 30, show=False)
        except:
            pass
