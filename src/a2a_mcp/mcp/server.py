import time
import threading
import logging
import os
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, g
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
from .config import config
from .security import security_manager
from .monitoring import monitoring

# Create logs directory if it doesn't exist
if config.LOG_FILE:
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

# Setup logging configuration
logging_config = {
    'level': config.LOG_LEVEL,
    'format': config.LOG_FORMAT,
    'handlers': [
        logging.StreamHandler()  # Always log to console
    ]
}

# Add file handler if log file is configured
if config.LOG_FILE:
    logging_config['handlers'].append(
        logging.FileHandler(config.LOG_FILE)
    )

# Configure logging
for handler in logging_config['handlers']:
    handler.setLevel(logging_config['level'])
    handler.setFormatter(logging.Formatter(logging_config['format']))

logger = logging.getLogger(__name__)
for handler in logging_config['handlers']:
    logger.addHandler(handler)
logger.setLevel(logging_config['level'])

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY

# Initialize JWT
jwt = JWTManager(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Explicitly set memory storage
)

@dataclass
class AgentData:
    last_seen: str
    status: str
    address: tuple
    api_key: str

# Validation schemas
class RegisterSchema(Schema):
    agent_id = fields.Str(required=True)
    api_key = fields.Str(required=True)

class HeartbeatSchema(Schema):
    status = fields.Str(required=False)

# In-memory storage
agents_lock = threading.Lock()
agents: Dict[str, AgentData] = {}

def rate_limited_jwt_required(limit_value):
    """Combine rate limiting and JWT verification"""
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit_value)
        @jwt_required
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.before_request
def before_request():
    """Record request start time for monitoring"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Record metrics after each request"""
    try:
        # Record response time
        if hasattr(g, 'start_time'):
            response_time = (time.time() - g.start_time) * 1000  # Convert to ms
            monitoring.record_metric('response_time', response_time)

        # Record error rate
        if response.status_code >= 400:
            monitoring.record_metric('error_rate', 1)

        # Update agent count
        with agents_lock:
            monitoring.record_metric('agent_count', len(agents))

        return response
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        return response

@app.route('/health')
def health_check():
    """Get system health status"""
    return jsonify(monitoring.get_system_health())

@app.route('/metrics/<name>')
@rate_limited_jwt_required("30/minute")
def get_metric(name):
    """Get historical data for a specific metric"""
    window = request.args.get('window', 3600, type=int)
    return jsonify(monitoring.get_metric_history(name, window))

@app.route('/register', methods=['POST'])
@limiter.limit(config.REGISTER_RATE_LIMIT)
def register_agent():
    """Register a new agent with API key"""
    try:
        # Validate input
        schema = RegisterSchema()
        data = schema.load(request.get_json())
        
        agent_id = data['agent_id']
        api_key = data['api_key']
        
        # Validate API key
        if not security_manager.validate_api_key(agent_id, api_key):
            logger.warning(f"Invalid API key for agent: {agent_id}")
            return jsonify({'error': 'invalid api key'}), 401
        
        with agents_lock:
            if len(agents) >= config.MAX_AGENTS:
                logger.warning(f"Max agent limit reached, rejecting {agent_id}")
                return jsonify({'error': 'maximum agents limit reached'}), 503
                
            agents[agent_id] = AgentData(
                last_seen=datetime.now().isoformat(),
                status='active',
                address=(request.remote_addr, request.environ.get('REMOTE_PORT')),
                api_key=api_key
            )
            
        # Generate JWT token for future authentication
        access_token = security_manager.generate_token(agent_id)
        logger.info(f"Agent registered: {agent_id} from {request.remote_addr}")
        
        return jsonify({
            'status': 'registered',
            'agent_id': agent_id,
            'access_token': access_token
        })
        
    except ValidationError as err:
        logger.error(f"Registration validation error: {err.messages}")
        return jsonify({'error': err.messages}), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        monitoring.record_metric('error_rate', 1)
        return jsonify({'error': 'internal server error'}), 500

@app.route('/heartbeat/<agent_id>', methods=['POST'])
@rate_limited_jwt_required(config.HEARTBEAT_RATE_LIMIT)
def heartbeat(agent_id):
    """Update agent heartbeat with authentication"""
    try:
        # Verify token matches agent_id
        token_agent_id = get_jwt_identity()
        if token_agent_id != agent_id:
            logger.warning(f"Token mismatch: {token_agent_id} != {agent_id}")
            return jsonify({'error': 'unauthorized'}), 401

        schema = HeartbeatSchema()
        data = schema.load(request.get_json() or {})
        
        with agents_lock:
            if agent_id not in agents:
                logger.warning(f"Heartbeat from unknown agent: {agent_id}")
                return jsonify({'error': 'agent not found'}), 404
            
            agents[agent_id].last_seen = datetime.now().isoformat()
            if 'status' in data:
                agents[agent_id].status = data['status']
                
        return jsonify({'status': 'ok'})
        
    except ValidationError as err:
        logger.error(f"Heartbeat validation error: {err.messages}")
        return jsonify({'error': err.messages}), 400
    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")
        monitoring.record_metric('error_rate', 1)
        return jsonify({'error': 'internal server error'}), 500

@app.route('/status', methods=['GET'])
@rate_limited_jwt_required("30/minute")
def get_status():
    """Get status of all registered agents"""
    try:
        with agents_lock:
            agent_data = {
                id: {
                    'last_seen': data.last_seen,
                    'status': data.status,
                    'address': data.address
                } for id, data in agents.items()
            }
            
            return jsonify({
                'agents': agent_data,
                'total_agents': len(agents),
                'system_health': monitoring.get_system_health()
            })
    except Exception as e:
        logger.error(f"Status retrieval error: {str(e)}")
        monitoring.record_metric('error_rate', 1)
        return jsonify({'error': 'internal server error'}), 500

def cleanup_inactive_agents():
    """Remove agents that haven't sent a heartbeat in AGENT_TIMEOUT seconds"""
    while True:
        try:
            time.sleep(config.CLEANUP_INTERVAL)
            now = datetime.now()
            with agents_lock:
                for agent_id in list(agents.keys()):
                    last_seen = datetime.fromisoformat(agents[agent_id].last_seen)
                    if (now - last_seen).seconds > config.AGENT_TIMEOUT:
                        logger.info(f"Removing inactive agent: {agent_id}")
                        del agents[agent_id]
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            monitoring.record_metric('error_rate', 1)

def run_server(host=None, port=None):
    """Run the MCP server with configuration"""
    host = host or config.HOST
    port = port or config.PORT
    
    logger.info(f"Starting MCP Server on {host}:{port}")
    
    cleanup_thread = threading.Thread(target=cleanup_inactive_agents, daemon=True)
    cleanup_thread.start()
    
    app.run(
        host=host,
        port=port,
        debug=config.DEBUG
    )

if __name__ == '__main__':
    run_server()
