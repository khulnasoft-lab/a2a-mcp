import logging
from .cluster_registry import ClusterRegistry, ClusterInfo

logger = logging.getLogger("A2A-MCP.FederationController")

class FederationController:
    def __init__(self, local_cluster_id: str, registry: ClusterRegistry):
        """
        Initialize the FederationController for the local cluster.
        
        Parameters:
            local_cluster_id (str): Identifier of the local cluster used to distinguish this controller from remote peers.
        
        Notes:
            Stores a reference to `registry` for managing peer clusters.
        """
        self.local_cluster_id = local_cluster_id
        self.registry = registry

    def establish_peer(self, remote_cluster: ClusterInfo, credentials: dict):
        # Establish secure connection (e.g., mTLS handshake or WireGuard tunnel)
        """
        Attempt to establish a federation connection to a remote cluster and record it in the registry.
        
        Attempts to create a secure transport to the provided remote cluster (e.g., mTLS or WireGuard). Currently the transport setup is not implemented; the method records the remote cluster in the ClusterRegistry.
        
        Parameters:
            remote_cluster (ClusterInfo): Cluster metadata (id, API endpoint, etc.) for the remote peer to federate with.
            credentials (dict): Authentication material intended for establishing the secure connection. Accepted but not used by the current implementation.
        
        Side effects:
            - Adds or updates the remote cluster in the registry via self.registry.add_or_update_cluster(remote_cluster).
        """
        logger.info(f"Establishing federation with {remote_cluster.cluster_id} at {remote_cluster.api_endpoint}")
        # TODO: Implement actual secure transport setup
        self.registry.add_or_update_cluster(remote_cluster)

    def handle_peer_status_update(self, cluster_id: str, status: str):
        """
        Update the stored status of a federated peer cluster.
        
        If a cluster with the given cluster_id exists in the registry, set its `status` field to the provided value; otherwise do nothing.
        
        Parameters:
            cluster_id (str): Identifier of the peer cluster to update.
            status (str): New status value to assign to the cluster (e.g., "online", "offline", "degraded").
        """
        if cluster := self.registry.get_cluster(cluster_id):
            cluster.status = status
            logger.info(f"Cluster '{cluster_id}' status updated to {status}")

    def remove_peer(self, cluster_id: str):
        """
        Remove a federated peer from the local cluster registry.
        
        Removes the cluster identified by `cluster_id` from the controller's ClusterRegistry so it is no longer considered a federation peer.
        
        Parameters:
            cluster_id (str): Identifier of the remote cluster to remove.
        """
        logger.info(f"Removing federated peer {cluster_id}")
        self.registry.remove_cluster(cluster_id)
