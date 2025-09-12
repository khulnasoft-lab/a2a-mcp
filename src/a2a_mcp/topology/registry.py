from typing import Dict, Set, Callable
import threading

class TopologyRegistry:
    def __init__(self):
        """
        Initialize the registry.
        
        Creates empty sets for agent IDs and listener callables and a non-reentrant lock that guards access to those collections.
        
        Attributes:
            _agents (Set[str]): Set of registered agent identifiers.
            _listeners (Set[Callable]): Set of listener callables to notify on changes.
            _lock (threading.Lock): Non-reentrant mutex protecting _agents and _listeners.
        """
        self._agents: Set[str] = set()
        self._listeners: Set[Callable] = set()
        self._lock = threading.Lock()

    def register_agent(self, agent_id: str):
        """
        Register an agent ID and notify listeners of the change.
        
        Adds the given agent_id to the internal registry and triggers all registered listeners with a snapshot of current agents. Note: listeners are invoked while the registry lock is held; listener callbacks that interact with this registry (or otherwise block) can cause deadlocks.
        """
        with self._lock:
            self._agents.add(agent_id)
            self._notify_listeners()

    def deregister_agent(self, agent_id: str):
        """
        Remove an agent identifier from the registry and notify listeners of the change.
        
        If the given agent_id is present it is removed; if not present, the call is a no-op.
        After updating the registry, all registered listener callables are invoked with a
        snapshot of the current agents. The notification occurs while the registry lock is held.
        """
        with self._lock:
            self._agents.discard(agent_id)
            self._notify_listeners()

    def get_agents(self) -> Set[str]:
        """
        Return a thread-safe snapshot of currently registered agent IDs.
        
        Returns:
            Set[str]: A new set containing the registered agent identifiers (shallow copy). The caller may read or iterate this set without holding the registry lock; modifying it does not affect the registry's internal state.
        """
        with self._lock:
            return set(self._agents)

    def add_listener(self, fn: Callable):
        """
        Register a listener to be notified when the set of agents changes.
        
        The listener `fn` must be a callable that accepts a single argument: a snapshot (Set[str]) of the current agent IDs.
        Duplicate listeners are ignored (listeners are stored in a set). Registered listeners will be invoked synchronously
        when agents are registered or deregistered. There is no built-in mechanism to remove a listener.
        """
        self._listeners.add(fn)

    def _notify_listeners(self):
        """
        Notify all registered listener callables with a snapshot of the current agent IDs.
        
        Each listener in self._listeners is called with the set returned by self.get_agents().
        Note: get_agents() acquires the registry lock, so listeners are invoked while that lock
        may be held (risk of deadlock if listeners call back into the registry).
        """
        for fn in self._listeners:
            fn(self.get_agents())
