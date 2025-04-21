import asyncio
import logging
import time
from queue import Queue
import matplotlib
# Set the backend before importing pyplot
matplotlib.use('Qt5Agg')  # Switch to Qt backend instead of TkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading

from agents.agent_orchestrator import AgentOrchestrator
from market_maker.order_router import OrderRouter
from market_maker.data_router import DataRouter
from market_maker.database import Database
from frontend.test import TestOutput
from utils import *

# Disable logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(threadName)s] %(asctime)s - \t %(message)s',
)

logger = logging.getLogger(__name__)
# logging.disable(logging.CRITICAL)

# Add thread-safe data structures
plot_queue = Queue()
plot_lock = threading.Lock()
x_data = []
y_data = []

def plot_message(message: dict):
    with plot_lock:
        x_data.append(message['data']['timestamp'])
        y_data.append(message['data']['reference_price'])

fig, ax = plt.subplots()
line, = ax.plot(x_data, y_data)

def update(frame):
    # Process all available messages in the queue
    messages_to_plot = []
    while not plot_queue.empty():
        try:
            message = plot_queue.get_nowait()
            print(f"Received message: {message}")  # Debug print
            messages_to_plot.append(message)
        except Queue.Empty:
            break
    
    print(f"Messages to plot: {messages_to_plot}")  # Debug print
    if messages_to_plot:
        with plot_lock:
            for message in messages_to_plot:
                plot_message(message)
            line.set_data(x_data, y_data)
            print(f"\nUpdated plot data - x: {len(x_data)} points, y: {len(y_data)} points\n")  # Debug print
            ax.relim()
            ax.autoscale_view()
    
    return line,

def main():
    global agent_counter
    agent_counter = 1

    test_output = TestOutput(plot_queue)
    database = Database()
    order_router = OrderRouter(database)
    data_router = DataRouter(database)
    orchestrator = AgentOrchestrator()
    order_router.order_book.populate_for_testing()

    test_output.start()
    order_router.start()
    data_router.start()
    orchestrator.setup_dumb_agents(5)
    
    try:
        # Enable both the animation and the agent orchestration
        # orchestrator.run()
        # test_output.run()
        anim = FuncAnimation(fig, update, interval=100, blit=True)
        plt.show(block=True)

    except KeyboardInterrupt:
        logger.info("Shutting down...")

    finally:
        # Stop agents first and wait for them to finish
        try:
            orchestrator.stop()
            # Give more time for agents to cleanup their ZMQ connections
            time.sleep(2)  
            
            # Stop other components
            order_router.stop()
            data_router.stop()
            test_output.stop()
            
            # Wait for threads to finish
            order_router.join()
            data_router.join()
            test_output.join()
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

