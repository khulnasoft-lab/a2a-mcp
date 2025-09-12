import json
import time
from typing import Any, Dict, Callable

class AgentStateStreamer:
    def __init__(self, send_fn: Callable[[Dict[str, Any]], None]):
        """
        send_fn: Function to send serialized agent data to external platform.
        """
        self.send_fn = send_fn

    def stream_state(self, agent_id: str, state: Dict[str, Any]):
        data = {
            "agent_id": agent_id,
            "timestamp": time.time(),
            "state": state,
        }
        self.send_fn(data)

# Example adapter using WebSocket
import websocket

class WebSocketStateSender:
    def __init__(self, url: str):
        self.ws = websocket.create_connection(url)

    def __call__(self, data: Dict[str, Any]):
        self.ws.send(json.dumps(data))

# Usage in agent
# streamer = AgentStateStreamer(WebSocketStateSender("ws://digital-twin-host:port"))
# streamer.stream_state(agent_id, agent_state)
