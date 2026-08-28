import time
from features.protocol import make_msg, make_bye
from core.client import Client
from core.peer_manager import PeerManager


class Chat:
    def __init__(self, name: str, client: Client, peer_manager: PeerManager):
        """
        name         → this peer's display name
        client       → Client instance for sending messages
        peer_manager → PeerManager instance for getting peer list
        """
        self.name = name
        self.client = client
        self.peer_manager = peer_manager
        self.history = []  

    def send(self, text: str):
        """Send a chat message to all peers."""
        msg = make_msg(self.name, text)
        self.history.append(msg)
        peers = self.peer_manager.get_peers()
        self.client.broadcast(peers, msg)
        return msg

    def receive(self, ip: str, msg: dict):
        """Called by server when a message arrives."""
        if msg.get("type") == "MSG":
            self.history.append(msg)
            return msg
        return None

    def leave(self):
        """Broadcast BYE to all peers before disconnecting."""
        bye = make_bye(self.name)
        peers = self.peer_manager.get_peers()
        self.client.broadcast(peers, bye)

    def get_history(self) -> list:
        """Returns full chat history."""
        return self.history

    def format_message(self, msg: dict) -> str:
        """Formats a message dict for display."""
        ts = time.strftime("%H:%M", time.localtime(msg.get("timestamp", 0)))
        return f"[{ts}] {msg.get('from', 'unknown')}: {msg.get('text', '')}"
    
    def send_to_peer(self, ip: str, port: int, text: str) -> dict:
        """Send a direct message to one specific peer."""
        msg = make_msg(self.name, text)
        self.client.send(ip, port, msg)
        return msg