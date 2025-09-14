from typing import Dict, List, Optional

class AgentInfo:
    def __init__(self, agent_id: str, cluster_id: str, meta: dict):
        self.agent_id = agent_id
        self.cluster_id = cluster_id
        self.meta = meta

class CrossClusterDirectory:
    def __init__(self):
        # agent_id -> (AgentInfo)
        self._agents: Dict[str, AgentInfo] = {}

    def register_agent(self, agent: AgentInfo):
        self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str):
        if agent_id in self._agents:
            del self._agents[agent_id]

    def find_agent(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    def list_agents_by_cluster(self, cluster_id: str) -> List[AgentInfo]:
        return [a for a in self._agents.values() if a.cluster_id == cluster_id]
