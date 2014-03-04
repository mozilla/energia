import zmq
import json
import pickle

context = zmq.Context()

class Server:
    def __init__(self, args):
        self._args = args

        with open(args.config) as f:
            self._config = json.load(f)

        self._socket = context.socket(zmq.REP)
        self._socket.bind("tcp://*:8888")
        self._get_next_page = {"Darwin": self._page_generator("Darwin"),
                               "Linux": self._page_generator("Linux"),
                               "Windows": self._page_generator("Windows")}

    def _page_generator(self, os):
        for page in self._get_pages():
            for browser in self._get_browsers(os):
                yield page, browser

    def _get_pages(self):
        return self._config["Pages"]

    def _get_browsers(self, os):
        return self._config["OS"][os]

    def run(self):
        while True:
            header, payload = pickle.loads(self._socket.recv())

            if header == "get_configuration":
                self._send("config", (self._args, self._config))
                continue

            try:
                assert(header == "pull")
                page, browser = next(self._get_next_page[payload])
                self._send("page", (page, browser))
            except StopIteration:
                self._send("end")

    def _send(self, header, payload = None):
        msg = pickle.dumps((header, payload))
        self._socket.send(msg)
