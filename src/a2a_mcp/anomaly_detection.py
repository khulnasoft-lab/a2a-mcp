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
    """
    Return a list of per-agent metric dictionaries.
    
    Each item represents metrics reported by an agent, for example:
    {"agent_id": "agent-1", "connections": 12, "msg_rate": 80, "latency": 120, ...}
    
    Returns:
        List[Dict[str, Any]]: A list of metric dictionaries, one per agent. Implementations should return an empty list when no metrics are available.
    
    Note:
        This function is a placeholder and should be replaced with a real data source that collects or queries agent metrics.
    """
    return []

class AnomalyDetector:
    def __init__(
        self,
        metric_keys: List[str],
        on_anomaly: Callable[[Dict[str, Any]], None],
        history_window: int = 100,
        contamination: float = 0.02
    ):
        """
        Initialize the AnomalyDetector.
        
        Parameters:
            metric_keys: List of metric names that compose each feature vector; order defines the feature ordering used for training and detection.
            on_anomaly: Callback invoked for each detected anomaly. Called with the original metric dictionary for the anomalous sample.
            history_window: Maximum number of recent metric samples to retain for training (sliding window).
            contamination: Expected proportion of outliers used to configure the IsolationForest model.
        
        Notes:
            - A thread lock is created to protect concurrent access to internal history.
            - An IsolationForest model is instantiated but not yet trained.
        """
        self.metric_keys = metric_keys
        self.on_anomaly = on_anomaly
        self.history_window = history_window
        self.history = []
        self.model = IsolationForest(contamination=contamination)
        self.lock = threading.Lock()
        self.running = False

    def add_metrics(self, metrics: List[Dict[str, Any]]):
        """
        Append new metric records to the detector's sliding history in a thread-safe manner.
        
        The provided list of per-agent metric dictionaries is extended into the internal
        history buffer while holding the instance lock; if the buffer exceeds
        history_window, it is truncated to the most recent history_window entries.
        
        Parameters:
            metrics (List[Dict[str, Any]]): Sequence of metric dictionaries to add (each item is a single sample).
        """
        with self.lock:
            self.history.extend(metrics)
            if len(self.history) > self.history_window:
                self.history = self.history[-self.history_window :]

    def train(self):
        """
        Train the internal IsolationForest model using the most recent history window.
        
        Copies up to `history_window` recent metric records under a lock, validates and coerces each record to a numeric feature vector using `metric_keys`, and fits the model if enough valid samples are available.
        
        Returns:
            bool: True if the model was trained (enough valid samples), False otherwise.
        
        Notes:
            - Rows missing keys or containing non-coercible values are skipped.
            - Requires at least max(10, 0.5 * history_window) valid rows to proceed.
            - The model is fitted in-place on the validated data.
        """
        with self.lock:
            if len(self.history) < self.history_window:
                return False
            window = list(self.history[-self.history_window:])
        # Validate and coerce outside the lock
        valid = []
        for idx, item in enumerate(window):
            try:
                valid.append([float(item[k]) for k in self.metric_keys])
            except (KeyError, TypeError, ValueError):
                logger.debug("Skipping invalid history row at %d: %s", idx, item)
        if len(valid) < max(10, int(0.5 * self.history_window)):
            return False
        X = np.asarray(valid, dtype=float)
        self.model.fit(X)
        logger.info("Trained anomaly detection model on %d samples.", len(valid))
        return True
    def detect(self, metrics: List[Dict[str, Any]]):
        """
        Detect anomalies in a batch of metric dictionaries using the trained IsolationForest model.
        
        Processes the provided list of per-agent metric dictionaries in the same order as given, builds a feature matrix using self.metric_keys, and asks the fitted model for predictions. If the model marks an instance as an anomaly (prediction == -1), the corresponding metric dictionary is passed to the on_anomaly callback. If the detector has not yet accumulated at least `history_window` samples, the method returns immediately and does nothing. Callback exceptions are caught to avoid interrupting detection.
        Parameters:
            metrics (List[Dict[str, Any]]): Batch of metric dictionaries to evaluate. Each dict must contain the keys listed in self.metric_keys with numeric values.
        """
        if len(self.history) < self.history_window:
            return
        X = np.array([[item[k] for k in self.metric_keys] for item in metrics])
        preds = self.model.predict(X)
        for i, pred in enumerate(preds):
            if pred == -1:
                # Anomaly detected
                payload = metrics[i]
                logger.warning("Anomaly detected for metrics: %s", payload)
                try:
                    self.on_anomaly(payload)
                except Exception:
                    logger.exception("on_anomaly callback failed")
    def run(self, interval: int = 10):
        """
        Run the detector loop: continuously fetch metrics, update history, train the model, and run detection.
        
        This method sets the detector into a running state and blocks the current thread while looping. On each iteration it:
        - calls fetch_agent_metrics() and, if any metrics are returned, appends them to the internal history,
        - attempts to train the IsolationForest model on the recent history,
        - if training succeeds, runs anomaly detection on the fetched metrics (which may invoke the configured on_anomaly callback for detected anomalies),
        - sleeps for `interval` seconds before the next iteration.
        
        Parameters:
            interval (int): Seconds to wait between iterations. Defaults to 10.
        
        Notes:
        - The loop runs until stop() is called (which sets the running flag to False).
        - This method runs in the calling thread; use start() to run the loop in a background daemon thread.
        """
        self.running = True
        while self.running:
            if metrics := fetch_agent_metrics():
                self.add_metrics(metrics)
                if self.train():
                    self.detect(metrics)
            time.sleep(interval)

    def start(self, interval: int = 10):
        """
        Start the anomaly detector loop in a background daemon thread.
        
        Starts a daemon thread that runs the detector's continuous run loop, which fetches metrics, updates history, trains the model when enough data is available, and performs detection at the specified interval.
        
        Parameters:
            interval (int): Seconds between consecutive run iterations (default 10).  
        """
        t = threading.Thread(target=self.run, args=(interval,), daemon=True)
        t.start()

    def stop(self):
        """
        Signal the detector's run loop to stop.
        
        Set the internal running flag to False so a background `run()` loop will exit
        at its next iteration. Safe to call from any thread; does not block or join
        the running thread.
        """
        self.running = False
