import zmq
import json
import pickle
import os
import threading
import functools

from pandas import DataFrame
    
_context = zmq.Context()

class Dispatcher:
    def __init__(self, args):
        self._args = args
        self._tmp_file = "tmp.csv"

        with open(args.config) as f:
            self._config = json.load(f)

        self._scatter_socket =  {}
        for os in self._config["OS"]:
            self._scatter_socket[os] = self._create_scatter_socket(os)

        self._gather_socket = _context.socket(zmq.PULL)
        self._gather_socket.bind("tcp://*:9003")

    def run(self):
        scatter = threading.Thread(target=self._scatter)
        scatter.start()
        df = self._gather()
        scatter.join()
        if os.path.exists(self._tmp_file):
            os.remove(self._tmp_file)
        return df

    def _create_scatter_socket(self, os):
        ports = {"Windows": 9000, "Darwin": 9001, "Linux": 9002}
        socket = _context.socket(zmq.PUSH)
        socket.setsockopt(zmq.SNDTIMEO, 5000)
        socket.bind("tcp://*:{}".format(ports[os]))
        return socket

    def _get_pages(self):
        return self._config["Pages"]

    def _get_browsers(self, os):
        return self._config["OS"][os]

    def _scatter(self):
        for os in self._config["OS"]:
            for page in self._get_pages():
                for browser in self._get_browsers(os):
                    socket = self._scatter_socket[os]
                    print("sending {}".format(page))

                    while True:
                        try:
                            self._send(socket, self._build_message(page, browser))
                            break
                        except zmq.error.Again:
                            print("Warning: no {} workers reachable, retrying...".format(os))

    def _gather(self):
        df = DataFrame()
        num_browsers = 0
        for os in self._config["OS"]:
            num_browsers = num_browsers + len(self._get_browsers(os))
        nmsg = len(self._config["Pages"]) * num_browsers
        nrcv = 0

        #TODO: Handle missing data
        while nrcv != nmsg:
            msg = pickle.loads(self._gather_socket.recv())
            df = df.append(msg)
            df.to_csv(self._tmp_file, float_format="%.3f") # better safe than sorry
            nrcv += 1

        return df

    def _build_message(self, page, browser):
        #TODO: Don't send everything
        return {"page": page, "browser": browser, "args": self._args, "config": self._config}

    def _send(self, socket, msg):
        msg = pickle.dumps(msg)
        socket.send(msg)
