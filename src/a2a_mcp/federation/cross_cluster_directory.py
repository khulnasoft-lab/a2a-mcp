from typing import Dict, List, Optional

class AgentInfo:
    def __init__(self, agent_id: str, cluster_id: str, meta: dict):
        """
        Initialize an AgentInfo container.
        
        Parameters:
            agent_id (str): Unique identifier for the agent.
            cluster_id (str): Identifier of the cluster the agent belongs to.
            meta (dict): Arbitrary metadata about the agent (e.g., capabilities, labels, addresses).
        """
        self.agent_id = agent_id
        self.cluster_id = cluster_id
        self.meta = meta

class CrossClusterDirectory:
    def __init__(self):
        # agent_id -> (AgentInfo)
        """
        Initialize the CrossClusterDirectory.
        
        Creates an empty in-memory registry stored on self._agents mapping agent_id (str) to AgentInfo.
        """
        self._agents: Dict[str, AgentInfo] = {}

    def register_agent(self, agent: AgentInfo):
        """
        Register an agent in the directory, adding or replacing the entry keyed by the agent's ID.
        
        Parameters:
            agent (AgentInfo): Agent information to store; the agent is stored under its `agent_id` and will overwrite any existing entry with the same ID.
        """
        self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the directory.
        
        Removes the AgentInfo associated with the given agent_id from the internal registry.
        If the agent_id is not present, the call is a no-op (no exception is raised).
        
        Parameters:
            agent_id (str): Identifier of the agent to remove.
        """
        if agent_id in self._agents:
            del self._agents[agent_id]

    def find_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """
        Return the registered AgentInfo for the given agent_id, or None if not found.
        
        Parameters:
            agent_id (str): Unique identifier of the agent to look up.
        
        Returns:
            Optional[AgentInfo]: The AgentInfo associated with agent_id, or None when no entry exists.
        """
        return self._agents.get(agent_id)

    def list_agents_by_cluster(self, cluster_id: str) -> List[AgentInfo]:
        """
        Return all AgentInfo objects registered for the given cluster_id.
        
        Parameters:
            cluster_id (str): Cluster identifier to filter agents by.
        
        Returns:
            List[AgentInfo]: List of agents whose `cluster_id` equals the given `cluster_id`. Returns an empty list if none are found.
        """
        return [a for a in self._agents.values() if a.cluster_id == cluster_id]
