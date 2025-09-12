import threading
import time
import logging
from typing import Callable, List, Dict, Any
import numpy as np

from sklearn.ensemble import IsolationForest

logger = logging.getLogger("A2A-MCP.AnomalyDetection")

# Example telemetry fetcher (to be replaced with real agent/network data source)
def fetch_agent_metrics() -> List[Dict[str, Any]]:
    # Should return a list of dicts, e.g.:
    # [{"agent_id": "agent-1", "connections": 12, "msg_rate": 80, "latency": 120, ...}, ...]
    return []

class AnomalyDetector:
    def __init__(
        self,
        metric_keys: List[str],
        on_anomaly: Callable[[Dict[str, Any]], None],
        history_window: int = 100
    ):
        self.metric_keys = metric_keys
        self.on_anomaly = on_anomaly
        self.history_window = history_window
        self.history = []
        self.model = IsolationForest(contamination=0.02)
        self.lock = threading.Lock()
        self.running = False

    def add_metrics(self, metrics: List[Dict[str, Any]]):
        with self.lock:
            self.history.extend(metrics)
            if len(self.history) > self.history_window:
                self.history = self.history[-self.history_window :]

    def train(self):
        with self.lock:
            if len(self.history) < self.history_window:
                return False
            X = np.array([[item[k] for k in self.metric_keys] for item in self.history])
            self.model.fit(X)
            logger.info("Trained anomaly detection model.")
            return True

    def detect(self, metrics: List[Dict[str, Any]]):
        if len(self.history) < self.history_window:
            return
        X = np.array([[item[k] for k in self.metric_keys] for item in metrics])
        preds = self.model.predict(X)
        for i, pred in enumerate(preds):
            if pred == -1:
                # Anomaly detected
                logger.warning(f"Anomaly detected for metrics: {metrics[i]}")
                self.on_anomaly(metrics[i])

    def run(self, interval: int = 10):
        self.running = True
        while self.running:
            metrics = fetch_agent_metrics()
            if metrics:
                self.add_metrics(metrics)
                if self.train():
                    self.detect(metrics)
            time.sleep(interval)

    def start(self, interval: int = 10):
        t = threading.Thread(target=self.run, args=(interval,), daemon=True)
        t.start()

    def stop(self):
        self.running = False
