import asyncio
import zmq
import zmq.asyncio
from rich.live import Live
from rich.console import Console
import time

from order_book import OrderBook
from clearing_house import ClearingHouse
from utils import Order
from logger import Logger

class MarketMaker:
    def __init__(self):
        self.order_book = OrderBook()
        self.clearing_house = ClearingHouse()
        self.order_book.set_clearing_house(self.clearing_house)
        self.context = None
        self.socket = None
        self.console = None
        self.port = None
        self.logger = Logger()

    def setup(self, context: zmq.asyncio.Context, console: Console):
        self.context = context
        self.console = console
        
        # Try ports in range 5556-5566
        for port in range(5556, 5567):
            try:
                if self.socket:
                    self.socket.close(linger=0)
                    time.sleep(0.1)  # Give socket time to close
                
                self.socket = self.context.socket(zmq.REP)
                self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
                self.socket.bind(f"tcp://*:{port}")
                self.port = port
                self.logger.log(f"Market maker bound to port {port}")
                return port
            except zmq.ZMQError as e:
                self.logger.log(f"Port {port} is in use ({str(e)}), trying next port...")
                if self.socket:
                    self.socket.close(linger=0)
                    self.socket = None
                time.sleep(0.1)  # Give socket time to close
                continue
        
        raise RuntimeError("Could not find an available port in range 5556-5566")

    async def run(self):
        self.logger.log("Market maker started and waiting for orders...")
        
        try:
            # Initialize the live display
            with Live(self.order_book.print_table(), console=self.console, refresh_per_second=4) as live:
                while True:
                    try:
                        message = await self.socket.recv_json()
                        self.logger.log(f"Market maker received message: {message}")

                        order = Order.model_validate_json(message)
                        self.order_book.send_order(order)
                        
                        # Update the live display with the new table
                        live.update(self.order_book.print_table())

                        await self.socket.send_json({"status": "success"})
                    except zmq.ZMQError:
                        # Handle ZMQ errors during shutdown
                        break
        except asyncio.CancelledError:
            self.logger.log("Market maker shutting down...")
        finally:
            if self.socket:
                self.socket.close(linger=0)
            self.logger.log("Market maker cleanup complete.")

        
        