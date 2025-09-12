# Federated Multi-Cluster A2A Networking

## Overview

This module enables secure federation of multiple A2A MCP clusters, supporting:
- Secure inter-cluster peering and tunnel setup (mTLS or WireGuard)
- Unified cross-cluster agent discovery and directory
- Federated message routing with cluster-level failover and geo-resilience

## Key Components

- **Cluster Registry:** Tracks all known clusters, endpoints, and health.
- **Federation Controller:** Handles secure peering and status updates.
- **Cross-Cluster Directory:** Maintains a global agent registry.
- **Federated Router:** Routes messages across clusters, handles failover.

## Quickstart

1. Deploy MCP in each cluster and enable federation.
2. Configure peering endpoints and credentials in each cluster.
3. Use the FederationController to establish secure connections.
4. Register agents in the CrossClusterDirectory.
5. Use FederatedRouter to send messages—routing is transparent!

## Extending

- Implement secure transport for peering (see TODOs in code).
- Add geo-based routing and failover policies.
- Integrate cluster health monitoring for resilience.
