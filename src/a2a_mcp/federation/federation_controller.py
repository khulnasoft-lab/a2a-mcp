import logging
from .cluster_registry import ClusterRegistry, ClusterInfo

logger = logging.getLogger("A2A-MCP.FederationController")

class FederationController:
    def __init__(self, local_cluster_id: str, registry: ClusterRegistry):
        """
        Initialize the controller for managing federation peers.
        
        Parameters:
            local_cluster_id (str): Unique identifier of the local cluster; used to identify this node when establishing or managing federated peers.
        
        Attributes:
            local_cluster_id (str): Stored local cluster identifier.
            registry (ClusterRegistry): Cluster registry used to add, update, query, and remove peer cluster records.
        """
        self.local_cluster_id = local_cluster_id
        self.registry = registry

    def establish_peer(self, remote_cluster: ClusterInfo, credentials: dict):
        # Establish secure connection (e.g., mTLS handshake or WireGuard tunnel)
        """
        Initiate a secure federation with a remote cluster and register it in the cluster registry.
        
        Attempts to establish a secure transport (e.g., mTLS or WireGuard) to the provided remote cluster and records the cluster in the registry. Currently the secure transport setup is a TODO; the function always adds or updates the remote cluster via the registry.
        
        Parameters:
            remote_cluster (ClusterInfo): Cluster metadata (ID, API endpoint, etc.) for the peer to connect to.
            credentials (dict): Authentication/connection material intended for the secure transport (currently accepted but not applied).
        
        Side effects:
            - Adds or updates the remote cluster in the cluster registry.
        """
        logger.info(f"Establishing federation with {remote_cluster.cluster_id} at {remote_cluster.api_endpoint}")
        # TODO: Implement actual secure transport setup
        self.registry.add_or_update_cluster(remote_cluster)

    def handle_peer_status_update(self, cluster_id: str, status: str):
        """
        Update the recorded status of a peer cluster in the registry.
        
        If a cluster with the given cluster_id exists in the registry, updates its
        status attribute to the provided value and logs the change. If the cluster
        is not found, the call is a no-op.
        
        Parameters:
            cluster_id (str): Identifier of the peer cluster to update.
            status (str): New status value to assign to the cluster.
        """
        if cluster := self.registry.get_cluster(cluster_id):
            cluster.status = status
            logger.info(f"Cluster '{cluster_id}' status updated to {status}")

    def remove_peer(self, cluster_id: str):
        """
        Remove a federated peer from the cluster registry.
        
        Parameters:
            cluster_id (str): Identifier of the peer cluster to remove.
        """
        logger.info(f"Removing federated peer {cluster_id}")
        self.registry.remove_cluster(cluster_id)
