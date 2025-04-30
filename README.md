# A2A vs MCP Agent Demo

This project demonstrates two different approaches to agent communication:
1. **Master Control Program (MCP)** - A centralized server-based approach where agents communicate through a central server
2. **Agent-to-Agent (A2A)** - A decentralized peer-to-peer approach where agents communicate directly with each other

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### MCP Server and Agents

1. Start the MCP server:
```bash
python cli.py run-mcp-server
```

2. In separate terminals, start one or more MCP agents:
```bash
python cli.py run-mcp-agent --agent-id agent1
python cli.py run-mcp-agent --agent-id agent2
```

The MCP server will track all connected agents and their status. You can view the status by opening http://localhost:5000 in your browser.

### A2A (Agent-to-Agent) Network

1. Start the first A2A agent:
```bash
python cli.py run-a2a-agent --agent-id a2a1 --port 5001
```

2. Start additional A2A agents, connecting them to existing agents:
```bash
python cli.py run-a2a-agent --agent-id a2a2 --port 5002 --peer localhost:5001
python cli.py run-a2a-agent --agent-id a2a3 --port 5003 --peer localhost:5001 --peer localhost:5002
```

A2A agents will automatically discover other agents through their initial peers. You can type messages in any agent's terminal to broadcast them to all connected agents.

## Architecture

### MCP (Master Control Program)

- Centralized server that tracks all agents
- Agents register with the server and maintain connection through heartbeats
- Server provides a web interface to monitor agent status
- Simple and reliable but has a single point of failure

### A2A (Agent-to-Agent)

- Decentralized peer-to-peer network
- Agents connect directly to each other
- Messages are flooded through the network
- More resilient but requires more complex coordination
- No single point of failure

## Project Structure

```
a2a_mcp/
├── agents/              # Agent implementations
│   ├── mcp_agent.py    # MCP-based agent
│   └── a2a_agent.py    # Peer-to-peer agent
├── mcp/                # MCP server implementation
│   └── server.py       # Flask-based MCP server
├── cli.py             # Command-line interface
└── requirements.txt   # Python dependencies
```

## Contributing

Feel free to submit issues and pull requests to improve the demonstration. 