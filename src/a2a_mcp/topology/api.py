from fastapi import FastAPI
from .registry import TopologyRegistry

def create_app(registry: TopologyRegistry):
    app = FastAPI()

    @app.get("/topology/agents")
    def list_agents():
        return {"agents": list(registry.get_agents())}

    @app.post("/topology/join")
    def agent_join(agent_id: str):
        registry.register_agent(agent_id)
        return {"status": "joined", "agent_id": agent_id}

    @app.post("/topology/leave")
    def agent_leave(agent_id: str):
        registry.deregister_agent(agent_id)
        return {"status": "left", "agent_id": agent_id}

    return app
