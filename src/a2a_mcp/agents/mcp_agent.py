import requests
import time
import threading
import logging
from datetime import datetime
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPAgent:
    def __init__(self, agent_id: str, mcp_url: str):
        self.agent_id = agent_id
        self.mcp_url = mcp_url.rstrip('/')
        self.running = False
        self.heartbeat_thread = None
        self.access_token: Optional[str] = None
        self.last_heartbeat_success = False
        self.start_time = time.time()
        self.session = requests.Session()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5

    def _get_headers(self) -> dict:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def register(self) -> bool:
        """Register with the MCP server"""
        try:
            # Generate a simple API key (in production, use proper key management)
            api_key = f"agent-{self.agent_id}-{time.time()}"
            
            response = self.session.post(
                f"{self.mcp_url}/register",
                json={
                    'agent_id': self.agent_id,
                    'api_key': api_key
                },
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            if not self.access_token:
                logger.error("No access token received from server")
                return False
                
            logger.info(f"Successfully registered with MCP as {self.agent_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register with MCP: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_heartbeat(self) -> bool:
        """Send heartbeat to MCP server with retry"""
        try:
            response = self.session.post(
                f"{self.mcp_url}/heartbeat/{self.agent_id}",
                json={'status': self.get_status()},
                headers=self._get_headers()
            )
            response.raise_for_status()
            self.last_heartbeat_success = True
            return True
            
        except requests.exceptions.RequestException as e:
            self.last_heartbeat_success = False
            logger.error(f"Failed to send heartbeat: {e}")
            raise  # Allow retry mechanism to handle it

    def get_status(self) -> str:
        """Get current agent status"""
        return "healthy" if self.last_heartbeat_success else "degraded"

    def check_health(self) -> dict:
        """Check agent's health status"""
        return {
            'status': self.get_status(),
            'uptime': time.time() - self.start_time,
            'last_heartbeat_success': self.last_heartbeat_success,
            'connected_to_mcp': bool(self.access_token)
        }

    def heartbeat_loop(self):
        """Continuously send heartbeats while running"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(5)  # Wait before retry on error

    def start(self):
        """Start the agent"""
        if self.register():
            self.running = True
            self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            logger.info(f"MCP Agent {self.agent_id} started")
        else:
            raise RuntimeError("Failed to start agent - registration failed")

    def stop(self):
        """Stop the agent"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        logger.info(f"MCP Agent {self.agent_id} stopped")

def run_agent(agent_id: str, mcp_url: str):
    """Run an MCP agent"""
    agent = MCPAgent(agent_id, mcp_url)
    try:
        agent.start()
        # Keep main thread alive and monitor health
        while True:
            health = agent.check_health()
            if health['status'] == 'degraded':
                logger.warning(f"Agent health degraded: {health}")
            time.sleep(60)  # Check health every minute
            
    except KeyboardInterrupt:
        logger.info("\nStopping agent...")
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        raise
    finally:
        agent.stop()
