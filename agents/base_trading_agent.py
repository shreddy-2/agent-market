import zmq
import threading
import asyncio
import random
import time
import logging
from datetime import datetime

from config import ZMQConfig
from utils import OrderSide, OrderType, Message, MessageType, Order

logger = logging.getLogger(__name__)

class BaseTradingAgent:
    def __init__(self, agent_id: int, context: zmq.Context):
        self.agent_id = agent_id

        # Init zmq sockets
        self.context = context
        self.order_socket = self.context.socket(zmq.PUSH)
        self.order_socket.connect(f"{ZMQConfig.ORDER_ROUTER_HOST}:{ZMQConfig.ORDER_ROUTER_PORT}")

        self.market_data_sub_socket = self.context.socket(zmq.SUB)
        self.market_data_sub_socket.connect(f"{ZMQConfig.DATA_ROUTER_PUB_HOST}:{ZMQConfig.DATA_ROUTER_PUB_PORT}")
        self.market_data_sub_socket.subscribe("")

        self.market_data_req_socket = self.context.socket(zmq.REQ)
        self.market_data_req_socket.connect(f"{ZMQConfig.DATA_ROUTER_REP_HOST}:{ZMQConfig.DATA_ROUTER_REP_PORT}")

        self.orchestrator_commands_socket = self.context.socket(zmq.SUB)
        self.orchestrator_commands_socket.connect(f"{ZMQConfig.ORCHESTRATOR_OUT_HOST}:{ZMQConfig.ORCHESTRATOR_OUT_PORT}")

        self.orchestrator_responses_socket = self.context.socket(zmq.PULL)
        self.orchestrator_responses_socket.connect(f"{ZMQConfig.ORCHESTRATOR_IN_HOST}:{ZMQConfig.ORCHESTRATOR_IN_PORT}")

        # Handle incoming messages with Poller
        self.poller = zmq.Poller()
        self.poller.register(self.market_data_sub_socket, zmq.POLLIN)
        self.poller.register(self.orchestrator_commands_socket, zmq.POLLIN)
        

    def send_order(self, order: Order):
        try:
            message = Message(message_type=MessageType.ORDER, data=order)
            self.order_socket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Error sending order: {e}")
            raise e

    def send_orchestrator_response(self, response: dict):
        try:
            message = Message(message_type=MessageType.ORCHESTRATOR_RESPONSE, data=response)
            self.orchestrator_responses_socket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Error sending orchestrator response: {e}")
            raise e

    def receive_messages(self):
        """Poll sockets for incoming messages and return list of all messages received"""
        try:
            socks = dict(self.poller.poll())
            messages = []

            if self.market_data_sub_socket in socks:
                message = Message(message_type=MessageType.MARKET_DATA, data=self.market_data_sub_socket.recv_json())
                messages.append(message)

            if self.orchestrator_commands_socket in socks:
                message = Message(message_type=MessageType.ORCHESTRATOR_COMMAND, data=self.orchestrator_commands_socket.recv_json())
                messages.append(message)

            return messages
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            raise e
    
    def close(self):
        self.market_data_sub_socket.close()
        self.orchestrator_commands_socket.close()
        self.orchestrator_responses_socket.close()
        self.order_socket.close()
    

class DumbTradingAgent(BaseTradingAgent, threading.Thread):
    def __init__(self, agent_id: int, context: zmq.Context):
        threading.Thread.__init__(self)
        self._running = True

        BaseTradingAgent.__init__(self, agent_id, context)

    def run(self):
        while self._running:
            try:
                # Wait for a random amount of time between trades
                time.sleep(random.uniform(1, 3))

                # messages = self.receive_messages()

                # TODO: Get latest market price from market data

                # Send random order to market maker
                center_price = 100
                self.send_random_order(center_price)

                # TODO: Send some info to orchestrator

            # except KeyboardInterrupt:
            #     self.stop()
            #     # pass

            except Exception as e:
                if self._running:
                    logger.error(f"Error in agent {self.agent_id}: {e}")

    def send_random_order(self, center_price: float):
        side = random.choice([OrderSide.BUY, OrderSide.SELL])
        deviance = 0.005

        # Some prices will overlap and the orders will be matched
        price = center_price + random.uniform(-(center_price * deviance), center_price * deviance)
        price = round(price, 2)

        quantity = random.randint(2, 50) * 10
        order = Order(side=side, quantity=quantity, order_type=OrderType.LIMIT, price=price, timestamp=None, account_id=self.agent_id)
        
        if self._running:
            logger.debug(f"AGENT {self.agent_id} sending order: {order}")
            self.send_order(order)

    def stop(self):
        self._running = False
        logger.info(f"AGENT {self.agent_id} stopping")
        time.sleep(0.1)
        self.close()
    