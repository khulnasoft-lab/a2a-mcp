import json
import time
from typing import Any, Dict, Callable

class AgentStateStreamer:
    def __init__(self, send_fn: Callable[[Dict[str, Any]], None]):
        """
        Initialize the AgentStateStreamer.
        
        The provided send_fn will be invoked by stream_state with a single dictionary payload containing:
        - "agent_id" (str)
        - "timestamp" (float, from time.time())
        - "state" (Dict[str, Any])
        
        send_fn must accept one argument (Dict[str, Any]) and is responsible for delivering that payload to the external platform.
        """
        self.send_fn = send_fn

    def stream_state(self, agent_id: str, state: Dict[str, Any]):
        """
        Stream the given agent state to the configured sender.
        
        Constructs a payload containing `agent_id`, a Unix timestamp (`timestamp`), and the provided `state` dict, then passes that payload to the streamer's configured send function.
        
        Parameters:
            agent_id (str): Identifier of the agent whose state is being sent.
            state (Dict[str, Any]): Arbitrary serializable state for the agent.
        
        Notes:
            - The payload sent to the send function has keys: `"agent_id"`, `"timestamp"`, and `"state"`.
            - Any exceptions raised by the configured send function will propagate to the caller.
        """
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
        """
        Initialize the WebSocketStateSender by opening a WebSocket connection.
        
        Parameters:
            url (str): WebSocket URL to connect to (e.g. "ws://host:port/path").
        
        Notes:
            Establishes the connection via websocket.create_connection(url) and stores it on self.ws.
            Connection errors from the websocket library will propagate to the caller.
        """
        self.ws = websocket.create_connection(url)

    def __call__(self, data: Dict[str, Any]):
        """
        Send a JSON-serialized payload over the established WebSocket connection.
        
        Parameters:
            data (Dict[str, Any]): Payload to serialize and send; must be JSON-serializable.
        """
        self.ws.send(json.dumps(data))

# Usage in agent
# streamer = AgentStateStreamer(WebSocketStateSender("ws://digital-twin-host:port"))
# streamer.stream_state(agent_id, agent_state)
