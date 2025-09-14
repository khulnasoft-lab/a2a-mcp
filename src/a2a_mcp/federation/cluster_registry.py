import threading
from typing import Dict, List, Optional

class ClusterInfo:
    def __init__(self, cluster_id: str, api_endpoint: str, status: str, meta: dict):
        self.cluster_id = cluster_id
        self.api_endpoint = api_endpoint
        self.status = status  # healthy | degraded | offline
        self.meta = meta      # geo, capabilities, etc

class ClusterRegistry:
    def __init__(self):
        self._clusters: Dict[str, ClusterInfo] = {}
        self._lock = threading.Lock()

    def add_or_update_cluster(self, cluster_info: ClusterInfo):
        with self._lock:
            self._clusters[cluster_info.cluster_id] = cluster_info

    def remove_cluster(self, cluster_id: str):
        with self._lock:
            if cluster_id in self._clusters:
                del self._clusters[cluster_id]

    def get_cluster(self, cluster_id: str) -> Optional[ClusterInfo]:
        with self._lock:
            return self._clusters.get(cluster_id)

    def list_clusters(self) -> List[ClusterInfo]:
        with self._lock:
            return list(self._clusters.values())
