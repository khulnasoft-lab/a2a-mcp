"""
A2A vs MCP Demo - Demonstration of different agent communication patterns
"""

__version__ = "0.1.0"

from .agent_monitor_service import start_agent_monitor

# Call this at MCP startup
def initialize_services():
    """
    Initialize runtime services for the MCP.
    
    Starts the agent monitoring service. Call this at MCP startup to begin agent monitoring. Exceptions from the underlying monitoring startup are not caught and will propagate to the caller.
    """
    start_agent_monitor()
