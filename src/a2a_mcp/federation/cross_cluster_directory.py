from typing import Dict, List, Optional

class AgentInfo:
    def __init__(self, agent_id: str, cluster_id: str, meta: dict):
        """
        Create an AgentInfo container for cross-cluster agent metadata.
        
        Parameters:
            agent_id (str): Unique identifier for the agent.
            cluster_id (str): Identifier of the cluster where the agent resides.
            meta (dict): Arbitrary metadata associated with the agent (stored as provided).
        """
        self.agent_id = agent_id
        self.cluster_id = cluster_id
        self.meta = meta

class CrossClusterDirectory:
    def __init__(self):
        # agent_id -> (AgentInfo)
        """
        Initialize an in-memory registry.
        
        Creates an empty private mapping `_agents` that stores AgentInfo objects keyed by agent_id (str).
        """
        self._agents: Dict[str, AgentInfo] = {}

    def register_agent(self, agent: AgentInfo):
        """
        Register or update an AgentInfo in the directory keyed by its agent_id.
        
        Stores the given AgentInfo in the internal registry, replacing any existing entry with the same agent_id. This mutates the directory's in-memory state.
        """
        self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str):
        """
        Remove an agent from the registry by its agent_id.
        
        If the agent_id exists in the directory, the corresponding AgentInfo is deleted.
        If the agent_id is not present, the method does nothing (no error is raised).
        
        Parameters:
            agent_id (str): Unique identifier of the agent to remove.
        """
        if agent_id in self._agents:
            del self._agents[agent_id]

    def find_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """
        Return the registered AgentInfo for the given agent_id, or None if no such agent exists.
        
        Parameters:
            agent_id (str): Unique identifier of the agent to look up.
        
        Returns:
            Optional[AgentInfo]: The AgentInfo associated with agent_id, or None if not registered.
        """
        return self._agents.get(agent_id)

    def list_agents_by_cluster(self, cluster_id: str) -> List[AgentInfo]:
        """
        Return all registered agents that belong to the given cluster.
        
        Filters the directory's agents and returns a list of AgentInfo objects whose
        cluster_id equals the provided cluster_id.
        
        Parameters:
            cluster_id (str): Cluster identifier used to match agents.
        
        Returns:
            List[AgentInfo]: List of agents registered under the specified cluster (empty if none).
        """
        return [a for a in self._agents.values() if a.cluster_id == cluster_id]
