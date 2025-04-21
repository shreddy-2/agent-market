import threading
import time
import zmq

from queue import Empty

from utils import Message, MessageType
from market_maker.database import Database  
from config import ZMQConfig

class DataRouter(threading.Thread):
    def __init__(self, database: Database):
        super().__init__()
        self._running = True
        self.database = database

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"{ZMQConfig.DATA_ROUTER_PUB_HOST}:{ZMQConfig.DATA_ROUTER_PUB_PORT}")

    def run(self):
        while self._running:
            try:
                snapshot = self.database.market_snapshot_queue.get(timeout=0.5)
                # print(f"\t\t\t\t DATA SNAPSHOT: {snapshot}")
                message = Message(message_type=MessageType.DATA_SNAPSHOT, data=snapshot)
                self.socket.send_json(message.model_dump())
            except Empty:
                continue

    def stop(self):
        self._running = False
        time.sleep(0.2)
        self.join()