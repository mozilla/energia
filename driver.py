import argparse
from benchmarks.PowerGadget import PowerGadgetBenchmark as PowerGadgetBenchmark

if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="Plot Power Gadget's logs in time and frequency domain",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-e", "--resolution", help="Sampling resolution in ms, if applicable", default=50, type=int)
    parser.add_argument("-d", "--duration", help="Collection duration in s", default=30, type=int)
    parser.add_argument("-i", "--iterations", help="Number of iterations", default=5, type=int)
    parser.add_argument("-o", "--output", help="Path of the final csv output", default="report.csv")
    parser.add_argument("-l", "--plot", help="Path of the final plot, if applicable", default="report.png")
    parser.add_argument("-p", "--path", help="Tool path", default="")
    parser.add_argument("-b", "--benchmark", help="Benchmark to run", default="power_gadget")
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    args = parser.parse_args()

    benchmark = None
    if args.benchmark == "power_gadget":
        benchmark = PowerGadgetBenchmark(args)

    benchmark.log()
