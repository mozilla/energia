import zmq
import json
import pickle
import os

from pandas import DataFrame, concat

_context = zmq.Context()

class Server:
    def __init__(self, args):
        self._args = args
        self._tmp_file = "tmp.csv"

        with open(args.config) as f:
            self._config = json.load(f)

        self._socket = _context.socket(zmq.REP)
        self._socket.setsockopt(zmq.RCVTIMEO, 30*60*1000)
        self._socket.bind("tcp://*:8888")

        self._get_next_page = {}
        self._exhausted = {}
        for os in self._config["OS"]:
            self._get_next_page[os] = self._page_generator(os)
            self._exhausted[os] = False

    def _page_generator(self, os):
        for page in self._get_pages():
            for browser in self._get_browsers(os):
                yield page, browser

    def _get_pages(self):
        return self._config["Pages"]

    def _get_browsers(self, os):
        return self._config["OS"][os]

    def run(self):
        self._nclients = 0
        df = DataFrame()

        while self._nclients != 0 or not all(self._exhausted.values()):
            header, payload = pickle.loads(self._socket.recv())

            if header == "get_configuration":
                self._handle_configuration()
            elif header == "pull":
                self._handle_page_pull(payload)
            elif header == "data":
                df = self._handle_data(df, payload)

        os.remove(self._tmp_file)
        return df

    def _handle_configuration(self):
        print("A client has connected")

        self._nclients += 1
        self._send("config", (self._args, self._config))

    def _handle_page_pull(self, payload):
        print("A client is pulling a page")

        try:
            page, browser = next(self._get_next_page[payload])
            self._send("page", (page, browser))
        except StopIteration:
            self._send("end")
            self._exhausted[payload] = True
        except KeyError:
            self._send("end")

    def _handle_data(self, df, payload):
        print("A client has disconnected")

        self._send("ack")

        if payload is None:
            return df

        self._nclients -=1
        df = payload.combine_first(df)
        df.to_csv(self._tmp_file, float_format="%.3f") # better safe than sorry
        return df

    def _send(self, header, payload = None):
        msg = pickle.dumps((header, payload))
        self._socket.send(msg)
