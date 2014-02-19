# energia

Power benchmarking utilities used to collect and plot data of the energy usage of different desktop browsers on Windows, OSX & Linux.

## Dependencies

* Intel's Power Gadget, turbostat & powertop on Linux
* Python 3 with numpy, scipy and rpy2
* R with ggplot2 and gridExtra
* On Linux the **msr** and **cpuid** modules have to be loaded

## Idle benchmark on Windows, OSX or Linux

```bash
python3 idle_benchmark.py -c config.json -e 50 -d 30 -i 5
```

The command will collect data about the idle usage of the browsers and the websites specified in the configuration file and produce a csv file and plot, if R and ggplot2 are available on the system.
