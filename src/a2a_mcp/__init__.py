"""
A2A vs MCP Demo - Demonstration of different agent communication patterns
"""

__version__ = "0.1.0"

from .agent_monitor_service import start_agent_monitor

# Call this at MCP startup
def initialize_services():
    start_agent_monitor()
