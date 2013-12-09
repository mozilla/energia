# power_logger

Power logger wraps Intel's Power Gadget providing a simple API and plotting facilities.

## Dependencies

* Intel's Power Gadget
* Python 3, numpy, scipy and matplotlib
* On Linux the **msr** and **cpuid** modules have to be loaded

## Example usage as command line tool

python3 power_logger.py -e 50 -d 30 -i 5
