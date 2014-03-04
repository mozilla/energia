# energia

Desktop Browser Power benchmarking Utility

## Dependencies

* Intel's Power Gadget, Intel's BLA (Win only)
* Python 3 with numpy & pandas

## Idle benchmark on Windows, OSX and Linux
The idle benchmark collects CPU & GPU statistics of the requested browsers idling on predefined pages.
The set of browsers and pages to benchmark can be specified in a json configuration file.
The collected metrics are aggregated from several tools which can also be specified in the configuration file, currently *energia* supports *PowerGadget* and *BLA*.
PowerGadget is the only tool available on all platforms. Finally, the aggregated results are stored in a csv file.

```bash
python3 benchmark.py -c config.json
```

The command will collect data about the idle usage of the browsers and the websites specified in the configuration file and produce a csv file.
