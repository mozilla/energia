from pandas import DataFrame

class Benchmark:
    def __init__(self, args):
        self._debug = args.debug
        self._duration = args.duration
        self._iterations = args.iterations
        self._output = args.output

    def _collect_power_usage(self):
        df = DataFrame(columns=self._fields)

        for i in range(0, self._iterations):
            if self._debug:
                print("Starting run", i)
            df = self._run_iteration(df)

        return df.convert_objects(convert_numeric=True)

    def _run_iteration(self, df):
        self.initialize_iteration()
        self._tool.start()
        self.execute_iteration()
        summary = self._tool.join()
        self.finalize_iteration()
        return df.append(summary, ignore_index=True)

    def log(self):
        self.initialize()
        df = self._collect_power_usage()
        df = self.filter_outliers(df)
        df.describe().to_csv(self._output) if self._output else None
        self.process_measurements(df)
        self.finalize()

    def initialize(self):
        pass

    def initialize_iteration(self):
        pass

    def execute_iteration(self):
        pass

    def filter_outliers(self, df):
        return df

    def finalize_iteration(self):
        pass

    def process_measurements(self, df):
        pass

    def finalize(self):
        pass
