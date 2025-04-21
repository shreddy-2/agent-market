from market_maker.database import Database
from market_maker.order_service import OrderBook
from utils import Message, MessageType, Order
from config import ZMQConfig

import threading
import zmq
import logging
import time

logger = logging.getLogger(__name__)

class OrderRouter(threading.Thread):
    def __init__(self, database: Database):
        # Handle threads
        super().__init__()
        self._running = True

        # Get global database, which contains orderbook and clearing house
        self.order_book = OrderBook(database)

        # Init zmq stuff, pulling ports from config file
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind(f"{ZMQConfig.ORDER_ROUTER_HOST}:{ZMQConfig.ORDER_ROUTER_PORT}")

    def run(self):
       logger.info("Order router running")
       while self._running:
           # Get message from socket
           try:
               message = self.socket.recv_json()
               logger.debug(f"Order router received message: {message}")
           except zmq.ZMQError:
               if self._running:
                   raise
           
           # If message is an order, send to order book
           if message.get("message_type") == "ORDER":
               if not self._running:
                   continue
               order = Order.model_validate_json(message.get("data"))
               logger.debug(f"Order router received order: {order}")
               self.order_book.send_order(order)
               logger.debug(f"MARKET MAKER: \n{self.order_book}\n")

    def stop(self):
        logger.info("Stopping order router")
        self._running = False
        time.sleep(0.2)  # Give time for last messages to process
        self.socket.close()
        self.context.term()
