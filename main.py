import time
import random
import asyncio
import zmq
import zmq.asyncio
from datetime import datetime
from rich.live import Live
from rich.console import Console
from enums import *

from utils import Order
from market_maker import MarketMaker
from logger import Logger

# Create shared instances
console = Console()
logger = Logger()

async def trading_agent(agent_id: int, context: zmq.asyncio.Context, port: int):
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
    socket.connect(f"tcp://localhost:{port}")
    
    logger.log(f"Agent {agent_id} started")
    
    try:
        while True:
            await asyncio.sleep(random.uniform(1, 3))
            # Send random market order
            side = random.choice([OrderSide.BUY, OrderSide.SELL])

            center_price = 100
            deviance = 0.005

            # Some prices will overlap and the orders will be matched
            price = center_price + random.uniform(-(center_price * deviance), center_price * deviance)
            price = round(price, 2)

            quantity = random.randint(2, 50) * 10
            order = Order(side=side, quantity=quantity, order_type=OrderType.LIMIT, price=price, timestamp=datetime.now(), account_id=agent_id)
            logger.log(f"Agent {agent_id} sending order: {order}")
            
            try:
                await socket.send_json(order.model_dump())
                response = await socket.recv_json()
                logger.log(f"Agent {agent_id} received response: {response}")
            except Exception as e:
                logger.log(f"Agent {agent_id} encountered error: {e}")
                await asyncio.sleep(1)  # Wait a bit before retrying
    except asyncio.CancelledError:
        logger.log(f"Agent {agent_id} shutting down...")
    finally:
        socket.close(linger=0)

if __name__ == "__main__":
    try:
        context = zmq.asyncio.Context()
        
        market_maker = MarketMaker()
        try:
            port = market_maker.setup(context, console)
        except Exception as e:
            logger.log(f"Failed to setup market maker: {e}")
            context.term()
            exit(1)
            
        order_book = market_maker.order_book

        # Populate order book with some initial orders
        order_book.populate_for_testing()

        async def main():
            # Create multiple trading agents
            num_agents = 3
            agent_tasks = [trading_agent(i+1, context, port) for i in range(num_agents)]
            
            # Create task group for easier cancellation
            async with asyncio.TaskGroup() as tg:
                # Start market maker
                market_maker_task = tg.create_task(market_maker.run())
                # Start agents
                agent_task_group = [tg.create_task(agent) for agent in agent_tasks]
                
                try:
                    # Wait for KeyboardInterrupt
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    # Cancel all tasks
                    market_maker_task.cancel()
                    for task in agent_task_group:
                        task.cancel()
                    raise

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.log("Shutdown initiated...")
    finally:
        logger.log("Cleaning up...")
        if market_maker and market_maker.clearing_house:
            market_maker.clearing_house.clear_orders()
        if market_maker and market_maker.socket:
            market_maker.socket.close(linger=0)
        if context:
            context.term()
        logger.log("Cleanup complete.")
