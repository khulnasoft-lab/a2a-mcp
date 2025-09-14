import json
import time
from typing import Any, Dict, Callable

class AgentStateStreamer:
    def __init__(self, send_fn: Callable[[Dict[str, Any]], None]):
        """
        Initialize the AgentStateStreamer with a transport callable.
        
        The provided send_fn will be invoked with a single payload dict containing
        "agent_id" (str), "timestamp" (float, time.time()), and "state" (Dict[str, Any]).
        send_fn is expected to accept that dict and perform the delivery (no return value required).
        """
        self.send_fn = send_fn

    def stream_state(self, agent_id: str, state: Dict[str, Any]):
        """
        Stream an agent's state to the configured transport.
        
        Builds a payload containing the agent's identifier, a UNIX timestamp (seconds since epoch), and the provided state dictionary, then forwards that payload to the transport function stored on the instance.
        
        Parameters:
            agent_id (str): Unique identifier of the agent whose state is being streamed.
            state (Dict[str, Any]): Serializable mapping of the agent's current state.
        
        Notes:
            The payload sent to the transport has the form:
                {"agent_id": agent_id, "timestamp": <float>, "state": state}
            This method has the side effect of calling the instance's send function; it does not return a value.
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
        Open a WebSocket connection to the given URL and store it on the instance.
        
        The connection is created synchronously via websocket.create_connection(url) and assigned to self.ws. No connection retry or error handling is performed by this initializer; failures during connection establishment will propagate to the caller.
        
        Parameters:
            url (str): WebSocket URL to connect to (e.g., "ws://host:port/path").
        """
        self.ws = websocket.create_connection(url)

    def __call__(self, data: Dict[str, Any]):
        """
        Send a JSON-serialized payload over the instance's WebSocket connection.
        
        Parameters:
            data (Dict[str, Any]): The payload to serialize to JSON and transmit. The dictionary should be JSON-serializable.
        
        Returns:
            None
        """
        self.ws.send(json.dumps(data))

# Usage in agent
# streamer = AgentStateStreamer(WebSocketStateSender("ws://digital-twin-host:port"))
# streamer.stream_state(agent_id, agent_state)
