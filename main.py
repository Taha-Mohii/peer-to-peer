import threading
import queue
from config import get_or_create_config, TCP_PORT, DISCOVERY_PORT
from utils.crypto import derive_key, hash_room_code
from core.discovery import Discovery
from core.peer_manager import PeerManager
from core.server import server
from core.client import Client
from features.chat import Chat


class LocalChat:
    def __init__(self, name: str, room_code: str):
        self.config = get_or_create_config(name)
        self.name = self.config["name"]
        self.room_code = room_code
        self.key = derive_key(room_code)
        self.message_queue = queue.Queue()

        # Core components
        self.peer_manager = PeerManager()
        self.client = Client(self.key)
        self.chat = Chat(self.name, self.client, self.peer_manager)

        # Server
        self.server = server(
            host="0.0.0.0", port=TCP_PORT, key=self.key, on_message=self._on_message
        )

        # Discovery
        self.discovery = Discovery(
            name=self.name,
            tcp_port=TCP_PORT,
            room_code=room_code,
            on_peer_found=self._on_peer_found,
        )

    def start(self):
        self.server.start()
        self.discovery.start()
        print(f"[LocalChat] Started as '{self.name}' in room '{self.room_code}'")
        self._input_loop()

    def _on_peer_found(self, ip: str, name: str, port: int):
        self.peer_manager.add_peer(ip, name, port)
        print(f"[LocalChat] {name} joined the room")

    def _on_message(self, ip: str, msg: dict):
        self.message_queue.put((ip, msg))
        self._process_messages()

    def _process_messages(self):
        while not self.message_queue.empty():
            ip, msg = self.message_queue.get()
            result = self.chat.receive(ip, msg)
            if result:
                print(self.chat.format_message(result))

    def _input_loop(self):
        print("Type messages and press Enter to send. Ctrl+C to quit.\n")
        try:
            while True:
                text = input()
                if text.strip():
                    msg = self.chat.send(text)
                    print(self.chat.format_message(msg))
        except KeyboardInterrupt:
            print("\n[LocalChat] Leaving room...")
            self.chat.leave()
            self.discovery.stop()
            self.server.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 main.py <your_name> <room_code>")
        sys.exit(1)

    name = sys.argv[1]
    room_code = sys.argv[2]
    app = LocalChat(name, room_code)
    app.start()
