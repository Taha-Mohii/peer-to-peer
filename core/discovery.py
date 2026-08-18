import socket
import threading
import json
import time
from utils.crypto import hash_room_code

DISCOVERY_PORT = 5001
BROADCAST_ADDR = "255.255.255.255"
HELLO_INTERVAL = 5


class Discovery:
    def __init__(self, name: str, tcp_port: int, room_code: str, on_peer_found):
        """
        name         → this peer's display name
        tcp_port     → port others should connect to for chat/file transfer
        room_code    → the shared room code entered by user
        on_peer_found → callback function called when a new peer is discovered
        """
        self.name = name
        self.tcp_port = tcp_port
        self.room_hash = hash_room_code(room_code)
        self.on_peer_found = on_peer_found
        self.running = False
        self.known_peers = {}  # ip -> peer info

    def start(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _broadcast_loop(self):
        """Repeatedly broadcasts HELLO every few seconds."""
        while self.running:
            self._send_hello()
            time.sleep(HELLO_INTERVAL)

    def _send_hello(self):
        """Sends a HELLO broadcast to the entire local network."""
        msg = json.dumps(
            {
                "type": "HELLO",
                "name": self.name,
                "port": self.tcp_port,
                "room": self.room_hash,
            }
        ).encode()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(msg, (BROADCAST_ADDR, DISCOVERY_PORT))

    def _send_ack(self, ip: str):
        """Sends HELLO_ACK directly to a specific peer."""
        msg = json.dumps(
            {
                "type": "HELLO_ACK",
                "name": self.name,
                "port": self.tcp_port,
                "room": self.room_hash,
            }
        ).encode()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(msg, (ip, DISCOVERY_PORT))

    def _listen(self):
        """Listens for HELLO and HELLO_ACK packets from other peers."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", DISCOVERY_PORT))
            s.settimeout(1.0)

            while self.running:
                try:
                    data, (ip, _) = s.recvfrom(1024)
                    self._handle_packet(data, ip)
                except socket.timeout:
                    continue

    def _handle_packet(self, data: bytes, ip: str):
        """Processes incoming UDP packets."""
        try:
            msg = json.loads(data.decode())
        except Exception:
            return

        # Ignore wrong room
        if msg.get("room") != self.room_hash:
            return

        msg_type = msg.get("type")
        name = msg.get("name")
        port = msg.get("port")

        if msg_type == "HELLO":
            # Someone is announcing themselves — send ACK back
            self._send_ack(ip)
            self._register_peer(ip, name, port)

        elif msg_type == "HELLO_ACK":
            # Someone acknowledged our HELLO
            self._register_peer(ip, name, port)

    def _register_peer(self, ip: str, name: str, port: int):
        """Adds peer to known list and fires callback if new."""
        local_ip = socket.gethostbyname(socket.gethostname())
        if ip == local_ip:
            return

        if ip not in self.known_peers:
            self.known_peers[ip] = {"name": name, "port": port}
            print(f"[Discovery] Found peer: {name} at {ip}:{port}")
            self.on_peer_found(ip, name, port)
