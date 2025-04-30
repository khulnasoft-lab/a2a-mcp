import time
import threading
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
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

@dataclass
class MetricPoint:
    timestamp: float
    value: float

@dataclass
class Metric:
    name: str
    description: str
    points: List[MetricPoint] = field(default_factory=list)
    retention_period: int = 3600  # 1 hour default retention

    def add_point(self, value: float):
        """Add a new data point"""
        now = time.time()
        self.points.append(MetricPoint(now, value))
        self._cleanup_old_points()

    def _cleanup_old_points(self):
        """Remove points older than retention period"""
        cutoff = time.time() - self.retention_period
        self.points = [p for p in self.points if p.timestamp > cutoff]

    def get_average(self, window_seconds: int = 300) -> Optional[float]:
        """Get average value over the last window_seconds"""
        if not self.points:
            return None
        cutoff = time.time() - window_seconds
        recent_points = [p.value for p in self.points if p.timestamp > cutoff]
        return sum(recent_points) / len(recent_points) if recent_points else None

class MonitoringSystem:
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        self.start_time = time.time()

        # Initialize standard metrics
        self.register_metric('agent_count', 'Number of connected agents')
        self.register_metric('message_rate', 'Messages per second')
        self.register_metric('error_rate', 'Errors per minute')
        self.register_metric('response_time', 'Average response time in ms')

    def register_metric(self, name: str, description: str, retention_period: int = 3600):
        """Register a new metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = Metric(name, description, retention_period=retention_period)

    def record_metric(self, name: str, value: float):
        """Record a value for a metric"""
        with self._lock:
            if name in self.metrics:
                self.metrics[name].add_point(value)
            else:
                logger.warning(f"Attempted to record unregistered metric: {name}")

    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        with self._lock:
            health = {
                'status': 'healthy',
                'uptime': time.time() - self.start_time,
                'metrics': {}
            }

            for name, metric in self.metrics.items():
                avg = metric.get_average()
                if avg is not None:
                    health['metrics'][name] = {
                        'current': avg,
                        'description': metric.description
                    }

            # Determine system health based on metrics
            error_rate = self.metrics['error_rate'].get_average(60)  # Last minute
            if error_rate and error_rate > 10:  # More than 10 errors per minute
                health['status'] = 'degraded'

            response_time = self.metrics['response_time'].get_average(300)  # Last 5 minutes
            if response_time and response_time > 1000:  # Response time > 1 second
                health['status'] = 'degraded'

            return health

    def get_metric_history(self, name: str, window_seconds: int = 3600) -> List[Dict]:
        """Get historical data for a metric"""
        with self._lock:
            if name not in self.metrics:
                return []
            
            metric = self.metrics[name]
            cutoff = time.time() - window_seconds
            return [
                {'timestamp': p.timestamp, 'value': p.value}
                for p in metric.points
                if p.timestamp > cutoff
            ]

# Global monitoring instance
monitoring = MonitoringSystem() 