from typing import Dict, Set, Callable
import threading

class TopologyRegistry:
    def __init__(self):
        self._agents: Set[str] = set()
        self._listeners: Set[Callable] = set()
        self._lock = threading.Lock()

    def register_agent(self, agent_id: str):
        with self._lock:
            self._agents.add(agent_id)
            self._notify_listeners()

    def deregister_agent(self, agent_id: str):
        with self._lock:
            self._agents.discard(agent_id)
            self._notify_listeners()

    def get_agents(self) -> Set[str]:
        with self._lock:
            return set(self._agents)

    def add_listener(self, fn: Callable):
        self._listeners.add(fn)

    def _notify_listeners(self):
        for fn in self._listeners:
            fn(self.get_agents())
