import time
import random
import asyncio
import zmq
import zmq.asyncio
from datetime import datetime
from rich.live import Live
from rich.console import Console
from enums import *

from utils import Order, Logger
from market_maker import MarketMaker
from agent import TradingAgent
# Create shared instances
console = Console()
logger = Logger()

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
        
        num_agents = 3
        agents = [TradingAgent(i+1, context, port) for i in range(num_agents)]

        async def main():
            # Create multiple trading agents
            agent_tasks = [agent.run_trades() for agent in agents]
            
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
