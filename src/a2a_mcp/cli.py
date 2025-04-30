import click
import sys
import os
import uuid

# Ensure the project directory is in the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import after adjusting path
try:
    from mcp import server as mcp_server
    from agents import mcp_agent
    from agents import a2a_agent
except ImportError as e:
    print(f"Error importing modules. Make sure structure is correct and requirements installed: {e}", file=sys.stderr)
    sys.exit(1)


@click.group()
def cli():
    """A CLI to run MCP and A2A agent demonstrations."""
    pass

# --- MCP Commands ---

@cli.command('run-mcp-server')
@click.option('--host', default='127.0.0.1', help='Host IP for the MCP server.')
@click.option('--port', default=5000, type=int, help='Port for the MCP server.')
@click.option('--production', is_flag=True, help='Run in production mode using Gunicorn.')
@click.option('--workers', default=None, type=int, help='Number of Gunicorn worker processes (default: 2x CPU cores + 1).')
@click.option('--max-requests', default=1000, type=int, help='Restart workers after handling this many requests.')
@click.option('--max-requests-jitter', default=100, type=int, help='Add randomness to max requests to avoid all workers restarting at once.')
def run_mcp(host, port, production, workers, max_requests, max_requests_jitter):
    """Starts the Master Control Program (MCP) web server."""
    if production and host == '127.0.0.1':
        print("Warning: In production mode, you might want to use '0.0.0.0' to accept external connections")
    
    print(f"Starting MCP Server on http://{host}:{port}")
    print("View agent status in your browser at the above address.")
    print("Press Ctrl+C to stop the server.")
    
    try:
        if production:
            import gunicorn.app.base
            import multiprocessing
            
            class GunicornApp(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if value is not None:  # Only set if value is not None
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            # Calculate default number of workers if not specified
            if workers is None:
                workers = (multiprocessing.cpu_count() * 2) + 1

            options = {
                'bind': f"{host}:{port}",
                'workers': workers,
                'worker_class': 'sync',
                'worker_tmp_dir': '/dev/shm',  # Use RAM for temp files
                'timeout': 120,
                'keepalive': 5,  # Keep-alive timeout
                'max_requests': max_requests,
                'max_requests_jitter': max_requests_jitter,
                'accesslog': '-',  # Log to stdout
                'errorlog': '-',   # Log to stderr
                'access_log_format': '%({x-real-ip}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"',
                'loglevel': 'info',
                # Security settings
                'limit_request_line': 4094,  # Limit request line size
                'limit_request_fields': 100,  # Limit number of header fields
                'limit_request_field_size': 8190,  # Limit header field sizes
            }
            
            from mcp.wsgi import application
            GunicornApp(application, options).run()
        else:
            mcp_server.run_server(host, port)
    except Exception as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        sys.exit(1)

@cli.command('run-mcp-agent')
@click.option('--agent-id', default=None, help='Unique ID for this agent (auto-generated if not set).')
@click.option('--mcp-url', default='http://127.0.0.1:5000', help='URL of the MCP server.')
def run_mcp_agent_cli(agent_id, mcp_url):
    """Starts an agent that connects to the MCP."""
    if agent_id is None:
        agent_id = f"mcp-agent-{uuid.uuid4().hex[:6]}"
    print(f"Starting MCP Agent '{agent_id}' connecting to {mcp_url}")
    print("Press Ctrl+C to stop the agent.")
    mcp_agent.run_agent(agent_id, mcp_url)


# --- A2A Commands ---

@cli.command('run-a2a-agent')
@click.option('--agent-id', default=None, help='Unique ID for this agent (auto-generated if not set).')
@click.option('--host', default='127.0.0.1', help='Host IP for this agent to listen on.')
@click.option('--port', default=0, type=int, help='Port for this agent (0 means random available port).')
@click.option('--peer', '-p', 'initial_peers', multiple=True, help='Initial peer address (HOST:PORT). Can specify multiple times.')
def run_a2a_agent_cli(agent_id, host, port, initial_peers):
    """Starts an Agent-to-Agent (A2A) communicating agent."""
    # Resolve port 0 to an actual available port
    if port == 0:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, 0))
                port = s.getsockname()[1]
        except Exception as e:
            print(f"Error finding an available port: {e}", file=sys.stderr)
            sys.exit(1)

    if agent_id is None:
        agent_id = f"a2a-{host}-{port}" # Default ID based on address

    print(f"Starting A2A Agent '{agent_id}' listening on {host}:{port}")
    if initial_peers:
        print(f"Attempting to connect to initial peers: {', '.join(initial_peers)}")
    print("Press Ctrl+C to stop the agent.")
    a2a_agent.run_agent(agent_id, host, port, initial_peers)


if __name__ == '__main__':
    # Add dummy __init__.py files if they don't exist, needed for imports
    for subdir in ['mcp', 'agents']:
         init_path = os.path.join(project_dir, subdir, '__init__.py')
         if not os.path.exists(init_path):
              with open(init_path, 'w') as f:
                   pass # Create empty file
    import socket
    os.environ["MCP_SECRET_KEY"] = "your-secret-key"
    os.environ["MCP_JWT_SECRET_KEY"] = "your-jwt-secret"
    cli()
