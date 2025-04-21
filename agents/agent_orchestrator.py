import zmq
import logging

from agents.base_trading_agent import DumbTradingAgent
from utils import mini_uuid
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.agents = []
        self.dumb_agents_context = zmq.Context()

    def setup_dumb_agents(self, num_agents: int):
        logger.info(f"Setting up {num_agents} dumb agents")
        for i in range(num_agents):
            agent = DumbTradingAgent(mini_uuid(), self.dumb_agents_context)
            self.agents.append(agent)
            agent.start()

    def run(self):
        for agent in self.agents:
            agent.run()

    def stop(self):
        logger.info("Stopping all agents")
        for agent in self.agents:
            agent.stop()
            agent.join()

        self.dumb_agents_context.term()

    
