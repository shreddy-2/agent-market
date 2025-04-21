import asyncio
import logging
import time
from queue import Queue
import threading

from frontend.test import TestOutput
from agents.agent_orchestrator import AgentOrchestrator
from market_maker.order_router import OrderRouter
from market_maker.data_router import DataRouter
from market_maker.database import Database
from utils import *

# Disable logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(threadName)s] %(asctime)s - \t %(message)s',
)

logger = logging.getLogger(__name__)
# logging.disable(logging.CRITICAL)


def main():
    global agent_counter
    agent_counter = 1

    test_output = TestOutput()
    database = Database()
    order_router = OrderRouter(database)
    data_router = DataRouter(database)
    orchestrator = AgentOrchestrator(5)
    order_router.order_book.populate_for_testing()

    test_output.start()
    order_router.start()
    data_router.start()
    orchestrator.start()
    # orchestrator.setup_dumb_agents(5)
    
    try:
        while True:
            # time.sleep(1)
            pass

    except KeyboardInterrupt:
        logger.info("Shutting down...")

    finally:
        # Stop agents first and wait for them to finish
        try:
            orchestrator.stop()
            # Give more time for agents to cleanup their ZMQ connections
            time.sleep(2)  
            logger.info("Orchestrator stopped")
            
            # Stop other components
            order_router.stop()
            logger.info("Order router stopped")
            data_router.stop()
            logger.info("Data router stopped")
            test_output.stop()
            logger.info("Test output stopped")
            
            # Wait for threads to finish
            order_router.join()
            logger.info("Order router joined")
            data_router.join()
            logger.info("Data router joined")
            test_output.join()
            logger.info("Test output joined")
            # Final cleanup
            order_router.order_book.clearing_house.clear_orders()
            logger.info("Shutdown complete\n")
            logger.info(f"Final order book:\n{order_router.order_book}")
            
        except KeyboardInterrupt:
            # Handle second interrupt more gracefully
            logger.error("Forced shutdown - some resources may not clean up properly")
            import sys
            sys.exit(1)


if __name__ == "__main__":
    main()

