import asyncio
import random
import zmq
import zmq.asyncio
from datetime import datetime
from enums import *

from utils import Order, Logger

class TradingAgent:
    """An automated trading agent that interacts with the market maker.
    Simulates a market participant by generating and sending random orders
    to the market maker via ZMQ sockets. Currently only sends random limit
    orders at random intervals.
    
    Attributes:
        agent_id (int): Unique identifier for this agent
        context (zmq.asyncio.Context): ZMQ context for network communication
        port (int): Port number where market maker is listening
        socket (zmq.Socket): ZMQ REQ socket for sending orders
        logger (Logger): Handles logging of agent operations
    """
    def __init__(self, agent_id: int, context: zmq.asyncio.Context, port: int):
        """Initialize a trading agent with connection to market maker.
        
        Args:
            agent_id (int): Unique identifier for the agent
            context (zmq.asyncio.Context): ZMQ context for socket creation
            port (int): Port number where market maker is listening
        """
        self.agent_id = agent_id
        self.context = context
        self.port = port

        self.logger = Logger()
        
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
        self.socket.connect(f"tcp://localhost:{self.port}")
        
        self.logger.log(f"Agent {self.agent_id} started")

    async def run_trades(self):
        """Run the agent's main trading loop.
        Continuously generates and sends random orders to the market maker.
        Implements random delays between trades to simulate realistic trading patterns.
        
        Raises:
            asyncio.CancelledError: When the agent is being shut down, log it
        """
        try:
            while True:
                # Wait for a random amount of time between trades
                await asyncio.sleep(random.uniform(1, 3))

                # TODO: Implement multiple realistic trading strategies
                # Send random market order
                side = random.choice([OrderSide.BUY, OrderSide.SELL])

                center_price = 100
                deviance = 0.005

                # Some prices will overlap and the orders will be matched
                price = center_price + random.uniform(-(center_price * deviance), center_price * deviance)
                price = round(price, 2)

                quantity = random.randint(2, 50) * 10
                order = Order(side=side, quantity=quantity, order_type=OrderType.LIMIT, price=price, timestamp=datetime.now(), account_id=self.agent_id)
                self.logger.log(f"Agent {self.agent_id} sending order: {order}")
                
                try:
                    await self.socket.send_json(order.model_dump())
                    response = await self.socket.recv_json()
                    self.logger.log(f"Agent {self.agent_id} received response: {response}")
                except Exception as e:
                    self.logger.log(f"Agent {self.agent_id} encountered error: {e}")
                    await asyncio.sleep(1)  # Wait a bit before retrying
                    
        except asyncio.CancelledError:
            self.logger.log(f"Agent {self.agent_id} shutting down...")
        finally:
            self.socket.close(linger=0)