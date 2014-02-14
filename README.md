# browser_power_utils

Power benchmarking utilities used to collect and plot data of the energy usage of different desktop browsers on Windows, OSX & Linux.

## Dependencies

* Intel's Power Gadget, turbostat & powertop on Linux
* Python 3 with numpy, scipy and rpy2
* R with ggplot2 and gridExtra
* On Linux the **msr** and **cpuid** modules have to be loaded

## Example usage as command line tool

```bash
python3 idle_logger.py -e 50 -d 30 -i 5
```
