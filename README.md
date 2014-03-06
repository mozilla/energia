# energia

Desktop Browser Power benchmarking Utility

## Dependencies

* Intel's Power Gadget, Intel's BLA (Win only)
* Python 3 with numpy, pandas & pyzmq
* ZeroMQ

Note that on Windows the WinPython distribution comes with all dependencies required.

## Idle benchmark on Windows, OSX and Linux
The idle benchmark collects CPU & GPU statistics of the requested browsers idling on predefined pages.
The set of browsers and pages to benchmark can be specified in a json configuration file.
The collected metrics are aggregated from several tools which can also be specified in the configuration file, currently *energia* supports *PowerGadget* and *BLA*.
*PowerGadget* is the only tool available on all platforms. Finally, the aggregated results are stored in a csv file.

```bash
python3 benchmark.py -c config.json
```

The command will collect data about the idle usage of the browsers and the websites specified in the configuration file and produce a csv file.

## Distributed execution
The benchmark supports distributed execution through a simple master-slave architecture.
To run the benchmark on a cluster, issue on each slave the following command:

```bash
python3 benchmark.py -a 192.168.0.1 # the address has to point to your master node
```

Finally launch the server process on a different node:

```bash
python3 benchmark.py --is_server ...
```

The server configuration will then be propagated to all slaves automatically and the websites 
partioned evenly among all of them. Once the execution is complete, a csv file is generated on the master node.
