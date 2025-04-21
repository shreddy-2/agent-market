import asyncio
import logging
import time

from agents.agent_orchestrator import AgentOrchestrator
from market_maker.order_router import OrderRouter
from market_maker.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(threadName)s] %(asctime)s - \t %(message)s',
)

logger = logging.getLogger(__name__)

def main():
    global agent_counter
    agent_counter = 1

    database = Database()
    order_router = OrderRouter(database)
    orchestrator = AgentOrchestrator()

    order_router.order_book.populate_for_testing()

    order_router.start()
    orchestrator.setup_dumb_agents(5)

    try:
        while True:
            orchestrator.run()
            time.sleep(0.1)  # Add small sleep to prevent CPU spinning

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # Stop agents first
        orchestrator.stop()
        time.sleep(0.5)  # Give agents time to stop
        # Then stop the order router
        order_router.stop()
        order_router.join()

        logger.info("Shutdown complete\n")
        order_router.order_book.clearing_house.clear_orders()
        logger.info(f"Final order book:\n{order_router.order_book}")


if __name__ == "__main__":
    main()

