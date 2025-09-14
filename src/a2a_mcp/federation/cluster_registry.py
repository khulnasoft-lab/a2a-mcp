import threading
from typing import Dict, List, Optional

class ClusterInfo:
    def __init__(self, cluster_id: str, api_endpoint: str, status: str, meta: dict):
        """
        Initialize a ClusterInfo instance.
        
        Parameters:
            cluster_id (str): Unique identifier for the cluster.
            api_endpoint (str): Base API endpoint (URL) used to reach the cluster.
            status (str): Cluster health status; expected values include "healthy", "degraded", or "offline".
            meta (dict): Arbitrary metadata about the cluster (e.g., geo location, capabilities).
        """
        self.cluster_id = cluster_id
        self.api_endpoint = api_endpoint
        self.status = status  # healthy | degraded | offline
        self.meta = meta      # geo, capabilities, etc

class ClusterRegistry:
    def __init__(self):
        """
        Initialize an empty, thread-safe cluster registry.
        
        Creates an internal mapping from cluster_id to ClusterInfo and a threading.Lock used to synchronize access to that mapping for concurrent callers.
        """
        self._clusters: Dict[str, ClusterInfo] = {}
        self._lock = threading.Lock()

    def add_or_update_cluster(self, cluster_info: ClusterInfo):
        """
        Add or update a cluster entry in the registry.
        
        This upserts the provided ClusterInfo into the registry keyed by its `cluster_id`.
        Operation is thread-safe and mutates the registry's internal storage.
        
        Parameters:
            cluster_info (ClusterInfo): Cluster information to store; `cluster_info.cluster_id` is used as the key.
        """
        with self._lock:
            self._clusters[cluster_info.cluster_id] = cluster_info

    def remove_cluster(self, cluster_id: str):
        """
        Remove the cluster with the given ID from the registry if it exists.
        
        This operation is thread-safe: it acquires the registry's internal lock and deletes the entry keyed by `cluster_id` from the internal storage. If no cluster with the given ID exists, the method is a no-op.
        
        Parameters:
            cluster_id (str): Identifier of the cluster to remove.
        """
        with self._lock:
            if cluster_id in self._clusters:
                del self._clusters[cluster_id]

    def get_cluster(self, cluster_id: str) -> Optional[ClusterInfo]:
        """
        Return the ClusterInfo for the given cluster_id, or None if not present.
        
        This method is thread-safe: it acquires the registry lock while accessing the internal store.
        
        Parameters:
            cluster_id (str): Identifier of the cluster to retrieve.
        
        Returns:
            Optional[ClusterInfo]: The ClusterInfo associated with `cluster_id`, or `None` if no entry exists.
        """
        with self._lock:
            return self._clusters.get(cluster_id)

    def list_clusters(self) -> List[ClusterInfo]:
        """
        Return a snapshot list of all registered ClusterInfo objects.
        
        The returned list contains the ClusterInfo instances currently stored in the registry.
        This operation acquires the registry lock to produce a consistent snapshot; callers
        should treat the list as a point-in-time view (the underlying registry may change
        after the call).
        
        Returns:
            List[ClusterInfo]: A list of ClusterInfo objects for all clusters currently registered.
        """
        with self._lock:
            return list(self._clusters.values())
