import zmq
import logging
import threading
import uvicorn

from collections import deque
from config import ZMQConfig
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
logger = logging.getLogger(__name__)

class TestOutput(threading.Thread):
    def __init__(self):
        super().__init__()
        self._running = True

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"{ZMQConfig.DATA_ROUTER_PUB_HOST}:{ZMQConfig.DATA_ROUTER_PUB_PORT}")
        self.socket.subscribe("")

        self.plot_buffer = deque(maxlen=100)

        self.app = FastAPI()
        self._setup_endpoint()

    def _setup_endpoint(self):
        @self.app.get("/plot_data")
        def get_plot_data():
            return JSONResponse(content={
                "timestamp": [x[0] for x in self.plot_buffer],
                "price": [x[1] for x in self.plot_buffer]
            })
        
        self.app.mount("/", StaticFiles(directory="frontend/static", html=True), name="static")

    def _run_server(self):
        uvicorn_config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=8000,
            # log_config=None,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
            }
        )
        uvicorn_server = uvicorn.Server(uvicorn_config)
        uvicorn_server.run()

    def run(self):
        logger.info("Test output running")
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()

        while self._running:
            message = self.socket.recv_json()
            logger.debug(f"TEST OUTPUT: {message}\n")
            if message['message_type'] == 'DATA_SNAPSHOT':
                self.plot_buffer.append((message['data']['timestamp'], message['data']['reference_price']))

    def stop(self):
        self._running = False
        self.socket.close()
        self.context.term()


