from fastapi import FastAPI
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    app = FastAPI()

    @app.get("/topology/agents")
    def list_agents():
        return {"agents": list(registry.get_agents())}

from fastapi import FastAPI
from pydantic import BaseModel
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    app = FastAPI()

    class AgentRequest(BaseModel):
        agent_id: str

    @app.get("/topology/agents")
    def list_agents():
        return {"agents": sorted(registry.get_agents())}

    @app.post("/topology/join")
    def agent_join(payload: AgentRequest):
        registry.register_agent(payload.agent_id)
        return {"status": "joined", "agent_id": payload.agent_id}

    @app.post("/topology/leave")
    def agent_leave(payload: AgentRequest):
        registry.deregister_agent(payload.agent_id)
        return {"status": "left", "agent_id": payload.agent_id}

    return app
