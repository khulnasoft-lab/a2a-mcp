import threading
from typing import Dict, List, Optional

class ClusterInfo:
    def __init__(self, cluster_id: str, api_endpoint: str, status: str, meta: dict):
        """
        Initialize a ClusterInfo data container.
        
        Parameters:
            cluster_id (str): Unique identifier for the cluster.
            api_endpoint (str): Base API endpoint (URL) used to contact the cluster.
            status (str): Current cluster health state; expected values include "healthy", "degraded", or "offline".
            meta (dict): Arbitrary metadata about the cluster (e.g., geographic region, capabilities).
        """
        self.cluster_id = cluster_id
        self.api_endpoint = api_endpoint
        self.status = status  # healthy | degraded | offline
        self.meta = meta      # geo, capabilities, etc

class ClusterRegistry:
    def __init__(self):
        """
        Initialize an empty, thread-safe cluster registry.
        
        Creates:
        - _clusters: dict mapping cluster_id (str) to ClusterInfo instances.
        - _lock: threading.Lock protecting access to the registry for concurrent use.
        """
        self._clusters: Dict[str, ClusterInfo] = {}
        self._lock = threading.Lock()

    def add_or_update_cluster(self, cluster_info: ClusterInfo):
        """
        Add or update a cluster entry in the registry in a thread-safe manner.
        
        If an entry with the same cluster_id already exists it will be replaced.
        
        Parameters:
            cluster_info (ClusterInfo): Cluster metadata to store (its cluster_id is used as the key).
        """
        with self._lock:
            self._clusters[cluster_info.cluster_id] = cluster_info

    def remove_cluster(self, cluster_id: str):
        """
        Remove a cluster from the registry if it exists.
        
        This method deletes the ClusterInfo associated with `cluster_id` from the registry.
        The operation is performed under the registry's internal lock, making it safe to call
        concurrently. If `cluster_id` is not present, the method is a no-op.
        
        Parameters:
            cluster_id (str): Identifier of the cluster to remove.
        """
        with self._lock:
            if cluster_id in self._clusters:
                del self._clusters[cluster_id]

    def get_cluster(self, cluster_id: str) -> Optional[ClusterInfo]:
        """
        Retrieve a ClusterInfo by its cluster_id in a thread-safe manner.
        
        Parameters:
            cluster_id (str): Identifier of the cluster to look up.
        
        Returns:
            Optional[ClusterInfo]: The ClusterInfo for the given cluster_id, or None if no such cluster is registered.
        """
        with self._lock:
            return self._clusters.get(cluster_id)

    def list_clusters(self) -> List[ClusterInfo]:
        """
        Return a snapshot list of all registered ClusterInfo objects.
        
        Acquires the registry lock and returns a new list containing the current ClusterInfo values; callers may modify the returned list without affecting the registry.
        """
        with self._lock:
            return list(self._clusters.values())
