import os
import jwt
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from .config import config

# Create logs directory if it doesn't exist
if config.LOG_FILE:
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:  # Only add handlers if none exist
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if configured
    if config.LOG_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.setLevel(config.LOG_LEVEL)

class SecurityManager:
    def __init__(self):
        # Generate or load encryption key
        self._encryption_key = os.environ.get('MCP_ENCRYPTION_KEY', Fernet.generate_key())
        self.fernet = Fernet(self._encryption_key)
        self._token_blacklist: Dict[str, datetime] = {}
        logger.info("Security manager initialized with encryption key")

    def generate_token(self, agent_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token for agent authentication"""
        payload = {
            'agent_id': agent_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'agent_auth'
        }
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')
        logger.debug(f"Generated token for agent {agent_id}")
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload if valid"""
        try:
            if token in self._token_blacklist:
                if datetime.utcnow() > self._token_blacklist[token]:
                    del self._token_blacklist[token]
                    logger.debug("Removed expired token from blacklist")
                else:
                    logger.warning("Attempt to use blacklisted token")
                    return None

            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'agent_auth':
                logger.warning("Invalid token type")
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def blacklist_token(self, token: str, expires_in: int = 3600):
        """Add token to blacklist"""
        self._token_blacklist[token] = datetime.utcnow() + timedelta(seconds=expires_in)
        logger.info(f"Token blacklisted for {expires_in} seconds")

    def encrypt_message(self, message: str) -> bytes:
        """Encrypt a message"""
        encrypted = self.fernet.encrypt(message.encode())
        logger.debug("Message encrypted")
        return encrypted

    def decrypt_message(self, encrypted_message: bytes) -> str:
        """Decrypt a message"""
        try:
            decrypted = self.fernet.decrypt(encrypted_message).decode()
            logger.debug("Message decrypted successfully")
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            raise

    def generate_api_key(self, agent_id: str) -> str:
        """Generate a secure API key for an agent"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{agent_id}-{timestamp}-{os.urandom(16).hex()}"
        api_key = hashlib.sha256(data.encode()).hexdigest()
        logger.info(f"Generated new API key for agent {agent_id}")
        return api_key

    def validate_api_key(self, agent_id: str, api_key: str) -> bool:
        """Validate an agent's API key"""
        valid = len(api_key) == 64 and all(c in '0123456789abcdef' for c in api_key.lower())
        if not valid:
            logger.warning(f"Invalid API key format for agent {agent_id}")
        return valid

# Global security manager instance
security_manager = SecurityManager() 