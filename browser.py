import platform
import os

class Browser:
    def __init__(self, name, path, page):
        self.page = page
        self.browser = path
        self.description = name
        self.path = path

    def get_name(self):
        return self.description

    def get_page(self):
        return self.page

    def get_path(self):
        return self.path

    def get_os(self):
        return platform.system()

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
        path = ""
        file = self.browser

        if os.path.isabs(self.browser):
            drive, path_and_file = os.path.splitdrive(self.browser)
            path, file = os.path.split(path_and_file)

        # We can't use Popen... terminate() doesn't shutdown the FF properly among all OSs
        os.system("start /D \"" + path + "\" " + file + " " + self.page)

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
