import sys
import shutil
import os
import platform
import multiprocessing
import tempfile

from wrapper import Wrapper

get_long_path = lambda x: x
try:
    import win32api
    get_long_path = win32api.GetLongPathName
except:
    pass


class IPPET(Wrapper):

    _win_exec = "ippet.exe"

    _avg_cpu = "Average CPU %"
    _avg_gpu = "Average GPU %"
    _tot_cpu = "Total CPU Watts"
    _tot_gpu = "Total GPU Watts"

    def __init__(self, args, browser):
        super().__init__(args)

        self.browser = browser
        self._fields = [self._tot_cpu, self._tot_gpu, self._avg_gpu, self._avg_cpu]
        self._system = platform.system()

        if self._args.path:
            if os.path.exists(self._args.path) and os.access(self._args.path, os.X_OK):
                self._tool = self._args.path
            else:
                raise Exception("IPPET executable not found")
        elif self._system == "Windows":
            if shutil.which(IPPET._win_exec):
                self._tool = IPPET._win_exec
            else:
                raise Exception("IPPET executable not found")
        else:
            raise Exception("IPPET does not support your operating system")

    def start(self):
        self._logfile = get_long_path(tempfile.mkdtemp()) + "\\"  # logfile specifies directory; ippet file is standard
        self._log_process = multiprocessing.Process(target=self._start)
        self._log_process.start()

    def _start(self):
        if self._system == "Windows":
            # 1st: enable_web: set to no
            # 2nd: z: do not zip files
            # 3rd: log_dir; file names are already specified
            # 4th: time_end: time interval for which it will run
            os.system("{} -enable_web {} -z {} -log_dir {} -time_end {} > NUL 2>&1".format(
                      self._tool, "n", "n", self._logfile, str(self._args.duration)))
        else:
            raise Exception("IPPET does not support your operating system")

    def join(self):
        self._log_process.join()
        return self._parse()

    def _parse(self):
        try:
            with open(self._logfile+"ippet_log_processes.xls") as f:  # append standard IPPET file
                summary = self.parse_data(f.readlines())

        except FileNotFoundError:
            raise Exception("IPPET failed to generate a valid logfile")
            return sys.exit(-1)


        assert(summary[self._tot_cpu] > 0)
        shutil.rmtree(self._logfile)  # deletes the data file

        return summary

    def parse_data(self, ippet_data):
            """
            This method takes the raw IPPET Log Data and returns a
            list of lists - each being a column from the original input.
            """

            ippet_data = "".join(ippet_data)  # for the case of a list input

            data_columns = []
            current_entry = ""
            is_complete_entry = False
            is_gathering_columns = True
            column_count = 0
            column_iterator = 0

            for entry in ippet_data:  # each "entry" is a character from the input
                if is_gathering_columns:  # column names are collected; each is within quotes
                    if current_entry == "" and entry != '"' and entry != "(" and entry != "\t":
                        is_gathering_columns = False  # name collection is complete, now populate
                        column_count -= 1  # solves 0-index problem
                    elif entry == '"' and is_complete_entry:
                        data_columns.append([current_entry])  # full name found; store it now
                        column_count += 1
                        current_entry = ""  # reset to empty string for new name
                        is_complete_entry = False  # next quote will begin entry
                    elif entry == '"' and not is_complete_entry:
                        is_complete_entry = True  # next quote will end entry
                    else:
                        current_entry += entry
                else:  # now, populate columns
                    if entry == "\t":  # entries are separated by a tab
                        if self.browser in data_columns[column_iterator % column_count][0]:
                            data_columns[column_iterator % column_count].append(float(current_entry))  # browser data

                        column_iterator += 1  # increment for next column entry
                        current_entry = ""  # reset to empty string for next entry

                        if column_iterator >= column_count:
                            column_iterator = 0  # reset to zero
                    else:
                        current_entry += entry  # append next digit to entry

            if column_count == 0:
                raise Exception("No data columns were found, the file is assumed invalid.")

            return self.get_browser_process_data(data_columns)

    def get_browser_process_data(self, data_columns):
        """
        The sum of current browser-specific data is returned.
        """

        browser_data = {self._tot_cpu: 0, self._tot_gpu: 0, self._avg_cpu: 0, self._avg_gpu: 0}

        for column in data_columns:
            if self.browser in column[0] and len(column) > 1:  # IPPET format is used to extract process names

                data_type = column[0][column[0].index(')')+2:]  # remove end paren and space
                if data_type == "CPU Power W":
                    browser_data[self._tot_cpu] += sum(column[1:])
                elif data_type == "GPU Power W":
                    browser_data[self._tot_gpu] += sum(column[1:])
                elif data_type == "%GPU":
                    browser_data[self._avg_gpu] += 0 if len(column[1:]) == 0 else sum(column[1:]) / len(column[1:])
                elif data_type == "%CPU":
                    browser_data[self._avg_cpu] += 0 if len(column[1:]) == 0 else sum(column[1:]) / len(column[1:])

        return browser_data

