from power_logger import PowerLogger
from subprocess import Popen
from time import sleep
import os

class IdleLogger(PowerLogger):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    # This method is run before all iterations
    def initialize(self):
        self.browser.initialize()
        sleep(5)
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
            self.browser = "FirefoxNightly.app"

    def initialize(self):
        os.system("open /Applications/" + self.browser + " --args " + self.page)

    def finalize(self):
        os.system('osascript -e \"tell application \\\"' + self.browser + '\\\" to quit\"')

    def __str__(self):
        return 'OSX, ' + self.browser + ', ' + self.page

#process = Popen(['/Applications/FirefoxNightly.app/Contents/MacOS/firefox-bin', '-new-window', 'www.cnn.com'], shell=True)

websites = ["about:blank", "www.youtube.com", "www.yahoo.com", "www.amazon.com", "www.ebay.com", "www.google.com",
            "www.facebook.com", "www.wikipedia.com", "www.craigslist.com"]

for page in websites:
    browser = OSXBrowser("firefox", page)
    logger = IdleLogger(browser)
    logger.log(50, 5, 20, show=False)
