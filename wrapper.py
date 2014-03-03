from pandas import DataFrame
from scipy import stats

class Wrapper:
    def __init__(self, args):
        self._args = args

    def log(self):
        df = DataFrame(columns=self._fields)

        for i in range(0, self._args.iterations):
            df = self._run_iteration(df)

        return self._compute_summary(df)

    def _compute_summary(self, df):
        df = df.convert_objects(convert_numeric=True)
        df = self._filter_outliers(df)

        summary = df.mean().to_dict()
        cis = df.apply(lambda x: stats.sem(x) * stats.t.ppf((1.95)/2., len(x) - 1)).to_dict()

        for key, value in cis.items():
            summary[key + " CI"] = value

        summary["iterations"] = self._args.iterations
        summary["duration"] = self._args.duration
        return DataFrame(summary, index=[0])

    def _filter_outliers(self, df):
        if len(df) <= 1:
            return df

        for c in df.columns:
            series = df[c]
            # SD is not robust
            df = df[(series >= series.median() - series.mad()*5) & (series <= series.median() + series.mad()*5)]

        return df

    def _run_iteration(self, df):
        self.start()
        summary = self.join()
        return df.append(summary, ignore_index=True)
