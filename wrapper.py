from pandas import DataFrame
from scipy import stats

class Wrapper:
    def __init__(self, args):
        self._args = args

    def log(self):
        df = DataFrame(columns=self._fields)

        for i in range(0, self._args.iterations):
            self.current_iteration = i  # allows for proper interval-file naming
            df = self._run_iteration(df)

        return self._compute_summary(df)

    def _compute_summary(self, df):
        df = df.convert_objects(convert_numeric=True)
        df, nfiltered = self._filter_outliers(df)

        summary = df.mean().to_dict()
        cis = df.apply(lambda x: stats.sem(x, ddof=1) * stats.t.ppf((1.95)/2., len(x) - 1)).to_dict()

        for key, value in cis.items():
            summary[key + " CI"] = value

        summary["Iterations"] = self._args.iterations - nfiltered
        summary["Duration"] = self._args.duration
        return DataFrame(summary, index=[0])

    def _filter_outliers(self, df):
        length = len(df)

        if length <= 1:
            return df, 0

        for c in df.columns:
            series = df[c]

            if series.isnull().any():
                continue

            # SD is not robust
            df = df[(series >= series.median() - series.mad()*5) & (series <= series.median() + series.mad()*5)]

        if length != len(df):
            print("Warning: {} outlier(s) removed.".format(length - len(df)))

        return df, length - len(df)

    def _run_iteration(self, df):
        self.start()
        summary = self.join()
        return df.append(summary, ignore_index=True)
