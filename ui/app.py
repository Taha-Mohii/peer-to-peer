import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import QThread, pyqtSignal

from config import get_or_create_config, TCP_PORT
from utils.crypto import derive_key
from storage.database import init_db
from core.discovery import Discovery
from core.peer_manager import PeerManager
from core.server import Server
from core.client import Client
from core.election import Election
from features.chat import Chat
from ui.launch_screen import LaunchScreen
from ui.chat_screen import ChatScreen


class MessageWorker(QThread):
    new_message = pyqtSignal(str, str, str, bool)  # from_name, text, timestamp, is_self

    def __init__(self, chat):
        super().__init__()
        self.chat = chat

    def run(self):
        pass


class App:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.window = QStackedWidget()
        self.window.setWindowTitle("LocalChat")

        self.chat_engine = None
        self.chat_screen = None

        self._show_launch()
        self.window.show()
        sys.exit(self.qt_app.exec_())

    def _show_launch(self):
        launch = LaunchScreen(on_join=self._on_join)
        self.window.addWidget(launch)
        self.window.setCurrentWidget(launch)

    def _on_join(self, name: str, room_code: str):
        config = get_or_create_config(name)
        key = derive_key(room_code)
        init_db()

        # Set up core components
        self.peer_manager = PeerManager()
        self.client = Client(key)
        self.chat_engine = Chat(name, self.client, self.peer_manager)

        self.server = Server(
            host="0.0.0.0", port=TCP_PORT, key=key, on_message=self._on_message
        )

        self.discovery = Discovery(
            name=name,
            tcp_port=TCP_PORT,
            room_code=room_code,
            on_peer_found=self._on_peer_found,
        )

        self.election = Election(
            device_id=config["device_id"],
            peer_manager=self.peer_manager,
            client=self.client,
            on_elected=self._on_elected,
        )

        self.server.start()
        self.discovery.start()

        # Run election after a short delay to let peers discover first
        threading.Timer(3.0, self.election.run).start()

        # Show chat screen
        self.chat_screen = ChatScreen(
            name=name,
            room_code=room_code,
            on_send=self._send_message,
            on_send_file=self._send_file,
        )
        self.window.addWidget(self.chat_screen)
        self.window.setCurrentWidget(self.chat_screen)
        self.window.setMinimumSize(600, 500)

    def _on_message(self, ip: str, msg: dict):
        """Called from server thread — update UI safely."""
        result = self.chat_engine.receive(ip, msg)
        if result and self.chat_screen:
            formatted = self.chat_engine.format_message(result)
            # Use invokeMethod to update UI from non-GUI thread
            from PyQt5.QtCore import QMetaObject, Qt

            QMetaObject.invokeMethod(
                self.chat_screen,
                "add_message",
                Qt.QueuedConnection,
                *self._make_args(result, is_self=False),
            )

    def _make_args(self, msg: dict, is_self: bool):
        import time
        from PyQt5.QtCore import Q_ARG

        ts = time.strftime("%H:%M", time.localtime(msg.get("timestamp", 0)))
        return [
            Q_ARG(str, msg.get("from", "unknown")),
            Q_ARG(str, msg.get("text", "")),
            Q_ARG(str, ts),
            Q_ARG(bool, is_self),
        ]

    def _on_peer_found(self, ip: str, name: str, port: int):
        self.peer_manager.add_peer(ip, name, port)
        if self.chat_screen:
            count = len(self.peer_manager.get_peers())
            from PyQt5.QtCore import QMetaObject, Qt

            QMetaObject.invokeMethod(
                self.chat_screen,
                "update_peers",
                Qt.QueuedConnection,
                *[__import__("PyQt5.QtCore", fromlist=["Q_ARG"]).Q_ARG(int, count)],
            )

    def _on_elected(self):
        print("[App] This peer is the host")

    def _send_message(self, text: str):
        msg = self.chat_engine.send(text)
        if self.chat_screen:
            import time

            ts = time.strftime("%H:%M", time.localtime(msg.get("timestamp", 0)))
            self.chat_screen.add_message(
                msg.get("from", ""), msg.get("text", ""), ts, is_self=True
            )

    def _send_file(self, filepath: str):
        import os
        from features.file_transfer import send_file

        filename = os.path.basename(filepath)
        # Copy to shared folder first
        import shutil

        shutil.copy(filepath, f"shared/{filename}")
        peers = self.peer_manager.get_peers()
        for ip, info in peers.items():
            threading.Thread(
                target=send_file,
                args=(ip, info["port"], filename, self.client.key),
                daemon=True,
            ).start()


if __name__ == "__main__":
    app = App()
