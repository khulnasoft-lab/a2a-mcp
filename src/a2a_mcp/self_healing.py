import logging
import subprocess

logger = logging.getLogger("A2A-MCP.SelfHealing")

def restart_agent(agent_id: str):
    # Replace with actual restart logic (e.g., via supervisor, k8s, ssh, etc)
    logger.info(f"Restarting agent: {agent_id}")
    # Example: subprocess.run(["systemctl", "restart", f"a2a-agent-{agent_id}"])
    # Simulate restart
    print(f"Simulated restart for agent {agent_id}")

def handle_anomaly(anomaly_data: dict) -> None:
    agent_id = anomaly_data.get("agent_id")
    if not agent_id:
        logger.error("Anomaly missing agent_id: %s", anomaly_data)
        return
    anomaly_type = infer_anomaly_type(anomaly_data)
    logger.warning(f"Anomaly detected for {agent_id}: {anomaly_type}")
    if anomaly_type == "disconnect":
        restart_agent(agent_id)
    elif anomaly_type == "message_storm":
        # Could throttle agent, notify admin, etc
        logger.warning(f"Throttling agent {agent_id} due to message storm.")
    elif anomaly_type == "latency_spike":
        # Remediation logic
        logger.warning(f"Latency spike detected for {agent_id}. Investigating...")
    # Extend for more anomaly types


def infer_anomaly_type(anomaly_data: dict) -> str:
def infer_anomaly_type(anomaly_data):
    # Simple rules - replace with more sophisticated logic if needed
    if anomaly_data.get("connections", 1) == 0:
        return "disconnect"
    if anomaly_data.get("msg_rate", 0) > 1000:
        return "message_storm"
    return "latency_spike" if anomaly_data.get("latency", 0) > 1000 else "unknown"
