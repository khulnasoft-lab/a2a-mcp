from fastapi import FastAPI
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    """
    Create and return a FastAPI application exposing topology endpoints.
    
    The returned app registers a GET /topology/agents endpoint which responds with
    a JSON object {"agents": [...]} where the list is populated from
    registry.get_agents().
    
    The registry argument is expected to provide a get_agents() iterable.
    Returns:
        FastAPI: An application instance ready to be mounted or served.
    """
    app = FastAPI()

    @app.get("/topology/agents")
    def list_agents():
        """
        Return a JSON-serializable mapping with the current agents from the topology registry.
        
        Returns:
            dict: A mapping with key "agents" whose value is a list converted from registry.get_agents().
        """
        return {"agents": list(registry.get_agents())}

from fastapi import FastAPI
from pydantic import BaseModel
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    """
    Create and return a FastAPI application exposing topology management endpoints.
    
    The returned app exposes:
    - GET /topology/agents
      - Returns JSON {"agents": [...]} containing a sorted list of agent IDs from the provided registry.
    - POST /topology/join
      - Accepts JSON payload {"agent_id": "<id>"}; registers the agent via the registry and returns {"status": "joined", "agent_id": "<id>"}.
    - POST /topology/leave
      - Accepts JSON payload {"agent_id": "<id>"}; deregisters the agent via the registry and returns {"status": "left", "agent_id": "<id>"}.
    
    The POST endpoints validate input against an internal Pydantic model with a single field `agent_id: str`. The function wires these routes to the given TopologyRegistry; calls to `/topology/join` and `/topology/leave` have the side effect of invoking the registry's register/deregister methods.
    
    Returns:
        FastAPI: A configured FastAPI application ready to be mounted by the caller.
    """
    app = FastAPI()

    class AgentRequest(BaseModel):
        agent_id: str

    @app.get("/topology/agents")
    def list_agents():
        """
        Return a sorted list of agent IDs from the topology registry.
        
        Returns:
            dict: JSON-serializable mapping with key "agents" to a list of agent ID strings sorted lexicographically.
        """
        return {"agents": sorted(registry.get_agents())}

    @app.post("/topology/join")
    def agent_join(payload: AgentRequest):
        """
        Register an agent from the POST payload and return a simple status object.
        
        Parameters:
            payload (AgentRequest): Request model containing `agent_id` — the identifier of the agent to register.
        
        Returns:
            dict: JSON-serializable dict with keys `status` ("joined") and `agent_id`.
        """
        registry.register_agent(payload.agent_id)
        return {"status": "joined", "agent_id": payload.agent_id}

    @app.post("/topology/leave")
    def agent_leave(payload: AgentRequest):
        """
        Handle an agent leaving the topology by deregistering it.
        
        Parameters:
            payload (AgentRequest): Request body containing the `agent_id` to remove.
        
        Returns:
            dict: JSON response {"status": "left", "agent_id": <agent_id>} confirming deregistration.
        """
        registry.deregister_agent(payload.agent_id)
        return {"status": "left", "agent_id": payload.agent_id}

    return app
