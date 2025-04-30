from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class ServerConfig:
    # Server settings
    HOST: str = '0.0.0.0'
    PORT: int = 5000
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.environ.get('MCP_SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY: str = os.environ.get('MCP_JWT_SECRET_KEY', 'dev-jwt-secret')
    
    # Agent settings
    CLEANUP_INTERVAL: int = 30  # seconds
    AGENT_TIMEOUT: int = 60     # seconds
    MAX_AGENTS: int = 1000
    
    # Rate limiting
    HEARTBEAT_RATE_LIMIT: str = "30/minute"
    REGISTER_RATE_LIMIT: str = "5/minute"
    
    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE: Optional[str] = 'logs/mcp_server.log'

config = ServerConfig() 