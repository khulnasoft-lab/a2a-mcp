from typing import Dict, Set, Callable
import threading

class TopologyRegistry:
    def __init__(self):
        """
        Initialize a TopologyRegistry.
        
        Creates an empty set of agent IDs, an empty set of listener callables, and a threading.Lock used to synchronize access to the agent set.
        """
        self._agents: Set[str] = set()
        self._listeners: Set[Callable] = set()
        self._lock = threading.Lock()

    def register_agent(self, agent_id: str):
        """
        Register an agent identifier in the registry and notify listeners of the change.
        
        This method is thread-safe: it acquires the registry's internal lock while updating the agent set.
        The operation is idempotent (adding an already-registered agent has no effect on the set), but listeners
        are still notified after the call. Registered listener callbacks are invoked with the current set of agent
        identifiers.
        
        Parameters:
            agent_id (str): Unique identifier of the agent to register.
        """
        with self._lock:
            self._agents.add(agent_id)
            self._notify_listeners()

    def deregister_agent(self, agent_id: str):
        """
        Remove an agent identifier from the registry and notify listeners of the change.
        
        This method acquires the registry lock, removes `agent_id` from the internal agent set (no error if the id is not present), and triggers listener callbacks with the updated agent snapshot. The operation is thread-safe.
        
        Parameters:
            agent_id (str): Identifier of the agent to remove.
        """
        with self._lock:
            self._agents.discard(agent_id)
            self._notify_listeners()

    def get_agents(self) -> Set[str]:
        """
        Return a thread-safe snapshot of registered agent identifiers.
        
        Returns:
            Set[str]: A copy of the currently registered agent IDs. The returned set is independent of the registry's internal state.
        """
        with self._lock:
            return set(self._agents)

    def add_listener(self, fn: Callable):
        """
        Register a callback to be notified when the set of agents changes.
        
        The callback `fn` will be called with a single argument: a snapshot Set[str] of current agent IDs.
        Duplicate registrations are ignored (listeners are stored in a set). This method does not synchronize access;
        if called concurrently with other registry operations the caller must ensure thread-safety.
        """
        self._listeners.add(fn)

    def _notify_listeners(self):
        """
        Notify all registered listener callbacks with the current set of agents.
        
        Each listener is called synchronously as `fn(agents_snapshot)`, where `agents_snapshot`
        is a shallow copy returned by `get_agents()`. Exceptions raised by a listener will
        propagate and may prevent subsequent listeners from being invoked.
        
        Listeners may be invoked while the registry's internal lock is held (callers such as
        `register_agent`/`deregister_agent` invoke this method under the lock). Listener
        implementations should avoid calling back into the registry (or otherwise blocking on
        the same lock) to prevent deadlocks.
        """
        for fn in self._listeners:
            fn(self.get_agents())
