import zmq
import logging
import threading
import time
from agents.base_trading_agent import DumbTradingAgent
from utils import mini_uuid

logger = logging.getLogger(__name__)

class AgentOrchestrator(threading.Thread):
    def __init__(self, num_dumb_agents: int):
        super().__init__()
        self._running = True   
        self.num_dumb_agents = num_dumb_agents
        self.agents = []
        self.dumb_agents_context = zmq.Context()

    def _setup_dumb_agents(self):
        logger.info(f"Setting up {self.num_dumb_agents} dumb agents")
        for _ in range(self.num_dumb_agents):
            agent = DumbTradingAgent(mini_uuid(), self.dumb_agents_context)
            self.agents.append(agent)
            agent.start()

    def run(self):
        self._setup_dumb_agents()
        while self._running:
            # Add a small sleep to prevent CPU spinning
            time.sleep(0.1)

    def stop(self):
        logger.info("Stopping all agents")
        self._running = False  # Set this first
        
        for agent in self.agents:
            agent.stop()
            agent.join()
            logger.debug(f"AGENT {agent.agent_id} joined")

        logger.info("Terminating agent ZMQ context")
        # Use linger=0 and timeout to prevent hanging
        # self.dumb_agents_context.setsockopt(zmq.LINGER, 0)
        self.dumb_agents_context.term()
        # # Add a timeout to force context termination
        # if not self.dumb_agents_context.closed:
        #     logger.warning("Force closing ZMQ context after timeout")
        #     self.dumb_agents_context.destroy(linger=0)
        logger.info("All agents stopped")
    
