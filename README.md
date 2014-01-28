# power_logger

Power logger wraps Intel's Power Gadget providing a simple API and plotting facilities.

![screenshot] (https://raw.github.com/vitillo/power_logger/master/screenshot.png)

## Dependencies

* Intel's Power Gadget
* Python 3 with numpy, scipy and matplotlib
* R with ggplot2 and gridExtra
* On Linux the **msr** and **cpuid** modules have to be loaded

## Example usage as command line tool

```
python3 power_logger.py -e 50 -d 30 -i 5
```
## Example usage through the API
```python
from power_logger import PowerLogger
from selenium import webdriver

class CnnLoad(PowerLogger):
    def __init__(self):
        super().__init__()
        self._driver = webdriver.Firefox()

    # This method is run before all iterations
    def initialize(self):
        pass

    # This method is run before the power profiling is enabled
    def initialize_iteration(self):
        self._driver.get("about:blank")

    # Everything in here runs with the power logger enabled
    def execute_iteration(self):
        self._driver.get("http://www.cnn.com")
        # Mark an event in time to appear in the final plots
        self.add_marker("page load")
        self._driver.get("http://www.cnn.com")
        self.add_marker("page load")
        self._driver.get("http://www.cnn.com")
        self.add_marker("page load")

    # This method is run after the power profiling has been disabled
    def finalize_iteration(self):
        self._driver.get("about:blank")

    # This method is run after all iterations
    def finalize(self):
        self._driver.quit()
        pass

logger = CnnLoad()
logger.log(50, 5)
