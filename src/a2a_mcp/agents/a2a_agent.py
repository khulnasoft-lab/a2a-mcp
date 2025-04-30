import socket
import threading
import time
import json
import random
import sys
import uuid
from datetime import datetime

class A2AAgent:
    def __init__(self, agent_id, host, port, initial_peers=None):
        self.agent_id = agent_id or f"a2a-agent-{uuid.uuid4().hex[:6]}"
        self.host = host
        self.port = int(port)
        self.address = (host, self.port)
        self.peers = set(initial_peers or [])
        self.peer_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.listener_thread = None
        self.speaker_thread = None
        self.status = "Initializing"
        self.running = False
        self.server_socket = None
        self.known_messages = set()  # For deduplication
        self.message_lock = threading.Lock()

        if initial_peers:
            for peer_str in initial_peers:
                try:
                    peer_host, peer_port = peer_str.split(':')
                    self.add_peer((peer_host, int(peer_port)))
                except ValueError:
                    print(f"[{self.agent_id}] Invalid initial peer format: {peer_str}. Use HOST:PORT.", file=sys.stderr)

    def _send_message(self, target_address, message_type, payload=None):
        """Sends a JSON message to a specific peer."""
        message = {
            'type': message_type,
            'sender_id': self.agent_id,
            'sender_address': self.address,
            'timestamp': time.time(),
            'payload': payload or {}
        }
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0) # Short timeout for connection attempt
                sock.connect(target_address)
                sock.sendall(json.dumps(message).encode('utf-8'))
            # print(f"[{self.agent_id}] Sent {message_type} to {target_address}")
            return True
        except socket.timeout:
            # print(f"[{self.agent_id}] Timeout connecting to peer {target_address}", file=sys.stderr)
            self.remove_peer(target_address) # Assume peer is down/unreachable
        except ConnectionRefusedError:
            # print(f"[{self.agent_id}] Connection refused by peer {target_address}", file=sys.stderr)
            self.remove_peer(target_address)
        except Exception as e:
            print(f"[{self.agent_id}] Error sending message to {target_address}: {e}", file=sys.stderr)
            self.remove_peer(target_address) # Remove potentially bad peer
        return False

    def add_peer(self, peer_address):
        """Adds a peer to the known list if it's not itself."""
        if peer_address != self.address:
            with self.peer_lock:
                if peer_address not in self.peers:
                    print(f"[{self.agent_id}] Discovered new peer: {peer_address}")
                    self.peers.add(peer_address)
                    return True
        return False

    def remove_peer(self, peer_address):
        """Removes a peer from the list."""
        with self.peer_lock:
            if peer_address in self.peers:
                print(f"[{self.agent_id}] Removing peer: {peer_address}")
                self.peers.discard(peer_address)

    def handle_connection(self, client_socket, address):
        """Handle incoming peer connection"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            message = json.loads(data)
            
            # Add sender to peers if not known
            sender_address = message.get('sender_address')
            if sender_address and sender_address not in self.peers:
                self.peers.add(sender_address)

            # Process message
            self.process_message(message)
            
        except Exception as e:
            print(f"Error handling connection from {address}: {e}")
        finally:
            client_socket.close()

    def process_message(self, message):
        """Process received message and forward to peers"""
        message_id = message.get('id')
        with self.message_lock:
            if message_id in self.known_messages:
                return  # Already processed this message
            self.known_messages.add(message_id)

        # Print received message
        print(f"Received from {message.get('sender_id')}: {message.get('content')}")

        # Forward to other peers (flood routing)
        self.forward_message(message)

    def forward_message(self, message):
        """Forward message to all known peers"""
        for peer in self.peers:
            if peer != f"{self.host}:{self.port}":  # Don't send to self
                try:
                    host, port = peer.split(':')
                    self.send_to_peer(host, int(port), message)
                except Exception as e:
                    print(f"Error forwarding to {peer}: {e}")

    def send_to_peer(self, host, port, message):
        """Send message to a specific peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            print(f"Error sending to {host}:{port}: {e}")

    def broadcast_message(self, content):
        """Broadcast a message to the network"""
        message = {
            'id': f"{self.agent_id}-{time.time()}",
            'sender_id': self.agent_id,
            'sender_address': f"{self.host}:{self.port}",
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.process_message(message)

    def start_server(self):
        """Start listening for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"A2A Agent {self.agent_id} listening on {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_connection,
                    args=(client_socket, address)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    print(f"Error accepting connection: {e}")

    def speak(self):
        """Periodically sends messages to known peers."""
        print(f"[{self.agent_id}] Speaker thread started.")
        self.status = "Starting speaker"
        while not self.stop_event.is_set():
            try:
                # Get a snapshot of peers to iterate over
                with self.peer_lock:
                    current_peers = list(self.peers) # Make a copy

                if not current_peers:
                    # print(f"[{self.agent_id}] Speaker: No known peers.")
                    self.status = "Seeking peers"
                    pass
                else:
                    # Choose a random peer to interact with
                    target_peer = random.choice(current_peers)

                    action = random.choice(['PING', 'GOSSIP', 'STATUS'])

                    if action == 'PING':
                        # print(f"[{self.agent_id}] Sending PING to {target_peer}")
                        self.status = f"Pinging {target_peer[0]}:{target_peer[1]}"
                        self._send_message(target_peer, 'PING')

                    elif action == 'GOSSIP':
                        # Share our list of known peers (convert set to list for JSON)
                        with self.peer_lock:
                            peer_list_payload = list(self.peers)
                        # print(f"[{self.agent_id}] Gossiping {len(peer_list_payload)} peers to {target_peer}")
                        self.status = f"Gossiping to {target_peer[0]}"
                        self._send_message(target_peer, 'GOSSIP_PEERS', {'peers': peer_list_payload})

                    elif action == 'STATUS':
                         # Send a simple status update
                         current_status = f"Agent {self.agent_id} is feeling {random.choice(['fine', 'busy', 'sleepy'])}"
                         # print(f"[{self.agent_id}] Sending status update to {target_peer}")
                         self.status = f"Sharing status with {target_peer[0]}"
                         self._send_message(target_peer, 'STATUS_UPDATE', {'status': current_status})

                # Wait before next action
                wait_time = random.uniform(5, 15) # Random interval
                self.stop_event.wait(wait_time)

            except Exception as e:
                 print(f"[{self.agent_id}] Unexpected error in speaker thread: {e}", file=sys.stderr)
                 self.status = "Speaker Error"
                 self.stop_event.wait(10) # Wait longer after an error


        print(f"[{self.agent_id}] Speaker thread stopped.")
        self.status = "Speaker stopped"

    def start(self):
        """Start the agent"""
        self.running = True
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Give listener a moment to bind port before speaker starts potentially removing peers
        time.sleep(0.5)

        if self.speaker_thread is None or not self.speaker_thread.is_alive():
             self.speaker_thread = threading.Thread(target=self.speak, daemon=True)
             self.speaker_thread.start()
        else:
             print(f"[{self.agent_id}] Speaker already running.")

        print(f"[{self.agent_id}] A2A Agent started. ID: {self.agent_id}, Address: {self.address}, Initial Peers: {[f'{p[0]}:{p[1]}' for p in self.peers]}")

    def stop(self):
        """Stop the agent"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"A2A Agent {self.agent_id} stopped")
        self.stop_event.set()
        threads_to_join = [self.listener_thread, self.speaker_thread]
        for thread in threads_to_join:
            if thread and thread.is_alive():
                thread.join(timeout=2) # Wait briefly for threads
        print(f"[{self.agent_id}] Agent stopped.")
        self.status = "Stopped"

def run_agent(agent_id, host, port, initial_peers):
    """Run an A2A agent"""
    agent = A2AAgent(agent_id, host, port, initial_peers)
    try:
        agent.start()
        # Interactive mode for sending messages
        print("Enter messages to broadcast (Ctrl+C to exit):")
        while True:
            try:
                message = input("> ")
                agent.broadcast_message(message)
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\nStopping agent...")
    finally:
        agent.stop()
