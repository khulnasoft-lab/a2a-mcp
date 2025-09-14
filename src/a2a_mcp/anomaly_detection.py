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
    
    Each item should be a dict containing an agent identifier and numeric metric values used by the anomaly detector, for example:
        {"agent_id": "agent-1", "connections": 12, "msg_rate": 80, "latency": 120, ...}
    
    Returns:
        List[Dict[str, Any]]: A list of metric dictionaries, one entry per agent. This function is currently a stub and should be implemented to fetch real metrics from the appropriate source.
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
            metric_keys (List[str]): Keys to extract numeric features from each metric dictionary.
            on_anomaly (Callable[[Dict[str, Any]], None]): Callback invoked with the metric dictionary for each detected anomaly.
            history_window (int, optional): Maximum number of recent metric entries to retain for training (default 100).
            contamination (float, optional): Expected proportion of outliers for the IsolationForest model (default 0.02).
        
        The constructor sets up an empty sliding history, creates an IsolationForest instance configured with
        the given contamination, and initializes a thread lock and a running flag used by the detector's
        background loop.
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
        Append a batch of per-agent metric dictionaries to the detector's sliding history.
        
        This method is thread-safe: it extends the internal history with the provided list of metric
        records and trims the stored history to the configured history_window (keeping the most
        recent entries).
        
        Parameters:
            metrics (List[Dict[str, Any]]): List of metric dictionaries (one per agent). Each dict
                is expected to contain the keys configured for this detector (see metric_keys).
        """
        with self.lock:
            self.history.extend(metrics)
            if len(self.history) > self.history_window:
                self.history = self.history[-self.history_window :]

    def train(self):
        """
        Attempt to train the IsolationForest model using the most recent sliding-window of history.
        
        Copies up to `history_window` recent metric records under the internal lock, validates and coerces the configured `metric_keys` to numeric features, and fits `self.model` when there are enough valid samples. Rows missing required keys or with non-numeric values are skipped. Training requires at least max(10, 50% of history_window) valid samples; otherwise the method returns False.
        
        Returns:
            bool: True if the model was successfully trained on sufficient valid samples, False otherwise.
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
        Detect anomalies in a batch of agent metrics using the trained IsolationForest model and invoke the anomaly callback for each outlier.
        
        This method requires that the detector has accumulated at least `history_window` samples (otherwise it returns immediately). For each input metric dictionary, a feature vector is constructed from `metric_keys` and scored by the current model; any sample predicted as an outlier (label -1) triggers `self.on_anomaly` with the original metric dictionary. Exceptions raised by the callback are caught and logged; they do not propagate.
        
        Parameters:
            metrics (List[Dict[str, Any]]): A list of metric dictionaries (one per agent). Each dict must contain all keys listed in `self.metric_keys`.
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
        Start the detector loop: periodically fetch metrics, update history, train the model when possible, and run anomaly detection on new batches.
        
        This method sets the internal `running` flag to True and enters a blocking loop that:
        - calls `fetch_agent_metrics()` each iteration,
        - appends any returned metrics to the sliding history,
        - attempts to train the IsolationForest on the current history,
        - if training succeeds, runs anomaly detection on the latest batch,
        - sleeps for `interval` seconds between iterations.
        
        Parameters:
            interval (int): Loop pause between iterations in seconds. The method blocks the calling thread until `stop()` is called; use `start()` to run this loop in a background thread.
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
        Start the detector loop in a background daemon thread.
        
        Runs self.run(interval) in a separate daemon thread so the detector collects metrics,
        trains the model, and performs detection periodically without blocking the caller.
        
        Parameters:
            interval (int): Polling interval in seconds passed to run(); controls how often
                metrics are fetched and processed. Defaults to 10.
        
        Returns:
            None
        """
        t = threading.Thread(target=self.run, args=(interval,), daemon=True)
        t.start()

    def stop(self):
        """
        Stop the detector's background run loop.
        
        Sets the internal `running` flag to False so the thread started by `start()` will exit its loop.
        This method does not join or wait for the background thread to finish; callers should join the thread if synchronous shutdown is required.
        """
        self.running = False
