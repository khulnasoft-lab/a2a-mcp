import logging
from .cluster_registry import ClusterRegistry, ClusterInfo

logger = logging.getLogger("A2A-MCP.FederationController")

class FederationController:
    def __init__(self, local_cluster_id: str, registry: ClusterRegistry):
        self.local_cluster_id = local_cluster_id
        self.registry = registry

    def establish_peer(self, remote_cluster: ClusterInfo, credentials: dict):
        # Establish secure connection (e.g., mTLS handshake or WireGuard tunnel)
        logger.info(f"Establishing federation with {remote_cluster.cluster_id} at {remote_cluster.api_endpoint}")
        # TODO: Implement actual secure transport setup
        self.registry.add_or_update_cluster(remote_cluster)

    def handle_peer_status_update(self, cluster_id: str, status: str):
        if cluster := self.registry.get_cluster(cluster_id):
            cluster.status = status
            logger.info(f"Cluster '{cluster_id}' status updated to {status}")

    def remove_peer(self, cluster_id: str):
        logger.info(f"Removing federated peer {cluster_id}")
        self.registry.remove_cluster(cluster_id)
