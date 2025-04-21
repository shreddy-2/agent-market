import zmq
import logging
import threading

from queue import Queue
from config import ZMQConfig

logger = logging.getLogger(__name__)

class TestOutput(threading.Thread):
    def __init__(self, plot_queue: Queue):
        super().__init__()
        self._running = True
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"{ZMQConfig.DATA_ROUTER_PUB_HOST}:{ZMQConfig.DATA_ROUTER_PUB_PORT}")
        self.socket.subscribe("")

        self.plot_queue = plot_queue


    def run(self):
        logger.info("Test output running")
        while self._running:
            message = self.socket.recv_json()
            # logger.info(f"TEST OUTPUT: {message}\n")
            self.plot_queue.put(message)

    def stop(self):
        self._running = False
        self.socket.close()
        self.context.term()


