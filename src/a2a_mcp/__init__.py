"""
A2A vs MCP Demo - Demonstration of different agent communication patterns
"""

__version__ = "0.1.0"

from .agent_monitor_service import start_agent_monitor

# Call this at MCP startup
def initialize_services():
    """
    Start package-level background services by launching the agent monitor.
    
    Call this at MCP startup to initialize monitoring; this function invokes start_agent_monitor().
    """
    start_agent_monitor()
