from fastapi import FastAPI
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    """
    Create and return a FastAPI application exposing topology endpoints.
    
    The returned app registers a GET /topology/agents endpoint that responds with JSON
    {"agents": [...]} where the list is constructed from the provided topology
    registry's get_agents() iterator.
    
    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI()

    @app.get("/topology/agents")
    def list_agents():
        """
        Return the current set of registered agents.
        
        Returns:
            dict: JSON-serializable mapping with key "agents" containing a list of agent IDs (list[str]).
        """
        return {"agents": list(registry.get_agents())}

from fastapi import FastAPI
from pydantic import BaseModel
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    """
    Create and return a FastAPI application exposing topology management endpoints.
    
    The returned app exposes three routes:
    - GET /topology/agents: returns JSON {"agents": [...]} with a sorted list of registered agent IDs.
    - POST /topology/join: accepts JSON {"agent_id": "<id>"} and registers that agent; returns {"status": "joined", "agent_id": "<id>"}.
    - POST /topology/leave: accepts JSON {"agent_id": "<id>"} and deregisters that agent; returns {"status": "left", "agent_id": "<id>"}.
    
    Returns:
        FastAPI: A FastAPI application instance with the above routes wired to the provided topology registry.
    """
    app = FastAPI()

    class AgentRequest(BaseModel):
        agent_id: str

    @app.get("/topology/agents")
    def list_agents():
        """
        Return a JSON-serializable dict containing the sorted list of agent IDs from the topology registry.
        
        Reads agent identifiers from the surrounding `registry` object and returns {"agents": [...]} where the list is sorted lexicographically.
        
        Returns:
            dict: A mapping with key "agents" to a list of sorted agent ID strings.
        """
        return {"agents": sorted(registry.get_agents())}

    @app.post("/topology/join")
    def agent_join(payload: AgentRequest):
        """
        Handle an agent join request by registering the agent and returning a confirmation.
        
        Parameters:
            payload (AgentRequest): Request payload containing `agent_id` to register.
        
        Returns:
            dict: JSON-serializable dict with keys:
                - "status": "joined"
                - "agent_id": the registered agent's id
        """
        registry.register_agent(payload.agent_id)
        return {"status": "joined", "agent_id": payload.agent_id}

    @app.post("/topology/leave")
    def agent_leave(payload: AgentRequest):
        """
        Deregister the agent specified in the request and return the leave status.
        
        Parameters:
            payload (AgentRequest): Pydantic model containing `agent_id` of the agent to remove from the topology.
        
        Returns:
            dict: JSON-serializable mapping with keys:
                - "status": fixed string "left"
                - "agent_id": the deregistered agent's id
        
        Side effects:
            Calls `registry.deregister_agent(agent_id)` to remove the agent from the registry.
        """
        registry.deregister_agent(payload.agent_id)
        return {"status": "left", "agent_id": payload.agent_id}

    return app
