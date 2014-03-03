from pandas import DataFrame
from scipy import stats

class Wrapper:
    def __init__(self, args):
        self._args = args
        self._listeners = []

    def add_listener(self, listener):
        pass

    def log(self):
        df = DataFrame(columns=self._fields)
        self._initialize()

        for i in range(0, self._args.iterations):
            df = self._run_iteration(df)

        self._finalize()
        return self._compute_summary(df)

    def _compute_summary(self, df):
        df = self._filter_outliers(df)

        summary = df.mean().to_dict()
        cis = df.apply(lambda x: stats.sem(x) * stats.t.ppf((1.95)/2., len(x) - 1)).to_dict()

        for key, value in cis.items():
            summary[key + " CI"] = value

        summary["iterations"] = self._args.iterations
        summary["duration"] = self._args.duration
        return DataFrame(summary, index=[0])

    def _filter_outliers(self, df):
        for c in df.columns:
            series = df[c]
            # SD is not robust
            df = df[(series >= series.median() - series.mad()*5) & (series <= series.median() + series.mad()*5)]

        return df

    def _run_iteration(self, df):
        self._initialize_iteration()
        self.start()
        self._execute_iteration()
        summary = self.join()
        self._finalize_iteration()
        return df.append(summary, ignore_index=True)

    def _initialize(self):
        for listener in self._listeners:
            listener.initialize()

    def _initialize_iteration(self):
        for listener in self._listeners:
            listener.initialize_iteration()

    def _execute_iteration(self):
        for listener in self._listeners:
            listener.execute_iteration()

    def _finalize_iteration(self):
        for listener in self._listeners:
            listener.finalize_iteration()

    def _finalize(self):
        for listener in self._listeners:
            listener.finalize()
