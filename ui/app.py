import os

os.environ["QT_SCALE_FACTOR"] = "2"

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
    new_message = pyqtSignal(str, str, str, bool)

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
        self.window.setStyleSheet("background-color: #1e1e2e;")
        self.dm_screens = {}

        self.chat_engine = None
        self.chat_screen = None

        self._show_launch()
        self.window.resize(500, 500)
        self.window.show()
        self._center_window()
        sys.exit(self.qt_app.exec_())

    def _center_window(self):
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - self.window.width()) // 2
        y = (screen.height() - self.window.height()) // 2
        self.window.move(x, y)

    def _show_launch(self):
        launch = LaunchScreen(on_join=self._on_join)
        self.window.addWidget(launch)
        self.window.setCurrentWidget(launch)

    def _on_join(self, name: str, room_code: str):
        config = get_or_create_config(name)
        key = derive_key(room_code)
        init_db()
        self.current_room_code = room_code
        self.key = key

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
        threading.Timer(3.0, self.election.run).start()

        self.chat_screen = ChatScreen(
            name=name,
            room_code=room_code,
            on_send=self._send_message,
            on_send_file=self._send_file,
            on_dm=self._open_dm,
        )
        self.window.addWidget(self.chat_screen)
        self.window.setCurrentWidget(self.chat_screen)
        self.window.setMinimumSize(600, 500)

    def _on_message(self, ip: str, msg: dict):
        result = self.chat_engine.receive(ip, msg)
        if result and self.chat_screen:
            from PyQt5.QtCore import QMetaObject, Qt

            QMetaObject.invokeMethod(
                self.chat_screen,
                "add_message",
                Qt.QueuedConnection,
                *self._make_args(result, is_self=False),
            )
            # Route to DM screen if open
            if ip in self.dm_screens:
                dm = self.dm_screens[ip]
                from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

                ts = time.strftime("%H:%M", time.localtime(result.get("timestamp", 0)))
                QMetaObject.invokeMethod(
                    dm,
                    "add_message",
                    Qt.QueuedConnection,
                    Q_ARG(str, result.get("from", "unknown")),
                    Q_ARG(str, result.get("text", "")),
                    Q_ARG(str, ts),
                    Q_ARG(bool, False),
                )

    def _make_args(self, msg: dict, is_self: bool):
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
            from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

            QMetaObject.invokeMethod(
                self.chat_screen,
                "update_peers",
                Qt.QueuedConnection,
                Q_ARG(int, count),
            )
            QMetaObject.invokeMethod(
                self.chat_screen,
                "add_peer",
                Qt.QueuedConnection,
                Q_ARG(str, ip),
                Q_ARG(str, name),
            )
            QMetaObject.invokeMethod(
                self.chat_screen,
                "add_notification",
                Qt.QueuedConnection,
                Q_ARG(str, f"{name} joined the room"),
            )

    def _on_elected(self):
        print("[App] This peer is the host")

    def _open_dm(self, ip: str, peer_name: str):
        from ui.dm_screen import DMScreen

        if ip in self.dm_screens:
            self.dm_screens[ip].raise_()
            return
        dm = DMScreen(
            my_name=self.chat_engine.name,
            peer_name=peer_name,
            peer_ip=ip,
            on_send=self._send_dm,
            on_send_file=self._send_file,
        )
        dm.show()
        self.dm_screens[ip] = dm

    def _send_dm(self, ip: str, text: str):
        peer = self.peer_manager.get_peer(ip)
        if peer:
            msg = self.chat_engine.send_to_peer(ip, peer["port"], text)
            if msg and ip in self.dm_screens:
                ts = time.strftime("%H:%M", time.localtime(msg.get("timestamp", 0)))
                self.dm_screens[ip].add_message(
                    msg.get("from", ""), msg.get("text", ""), ts, is_self=True
                )

    def _send_message(self, text: str):
        msg = self.chat_engine.send(text)
        if self.chat_screen:
            ts = time.strftime("%H:%M", time.localtime(msg.get("timestamp", 0)))
            self.chat_screen.add_message(
                msg.get("from", ""), msg.get("text", ""), ts, is_self=True
            )

    def _send_file(self, filepath: str):
        import shutil
        from features.file_transfer import send_file

        filename = os.path.basename(filepath)
        shutil.copy(filepath, f"shared/{filename}")
        peers = self.peer_manager.get_peers()
        for ip, info in peers.items():
            threading.Thread(
                target=send_file,
                args=(ip, info["port"], filename, self.key),
                daemon=True,
            ).start()


if __name__ == "__main__":
    app = App()
