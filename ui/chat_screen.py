import os
import threading
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFileDialog,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ChatScreen(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, name: str, room_code: str, on_send, on_send_file, on_dm):
        """
        on_dm → callback fired with (peer_ip, peer_name) when DM button clicked
        """
        super().__init__()
        self.name = name
        self.room_code = room_code
        self.on_send = on_send
        self.on_send_file = on_send_file
        self.on_dm = on_dm
        self.peer_widgets = {}  # ip -> QWidget
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"LocalChat — Room {self.room_code}")
        self.setMinimumSize(700, 550)
        self.setStyleSheet("background-color: #1e1e2e; font-family: Arial;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left: chat area ──────────────────────────────────
        chat_side = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(
            "background-color: #181825; border-bottom: 1px solid #313244;"
        )
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)

        room_label = QLabel(f"🔒  Room: {self.room_code}")
        room_label.setFont(QFont("Arial", 15, QFont.Bold))
        room_label.setStyleSheet("color: #cdd6f4;")
        header_layout.addWidget(room_label)

        header_layout.addStretch()

        self.peers_label = QLabel("● 0 peers")
        self.peers_label.setFont(QFont("Arial", 12))
        self.peers_label.setStyleSheet("color: #a6e3a1;")
        header_layout.addWidget(self.peers_label)

        header.setLayout(header_layout)
        chat_layout.addWidget(header)

        # Chat scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #1e1e2e; }
            QScrollBar:vertical { width: 6px; background: #1e1e2e; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; }
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #1e1e2e;")
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)

        # Input area
        input_area = QWidget()
        input_area.setFixedHeight(72)
        input_area.setStyleSheet(
            "background-color: #181825; border-top: 1px solid #313244;"
        )
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        file_btn = QPushButton("📎")
        file_btn.setFixedSize(46, 46)
        file_btn.setCursor(Qt.PointingHandCursor)
        file_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 10px;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover { background-color: #45475a; }
        """)
        file_btn.clicked.connect(self._on_file_clicked)
        input_layout.addWidget(file_btn)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setFixedHeight(46)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 10px;
                padding: 0px 16px;
                font-size: 15px;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
        """)
        self.text_input.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self.text_input)

        send_btn = QPushButton("Send")
        send_btn.setFixedSize(90, 46)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:pressed { background-color: #74c7ec; }
        """)
        send_btn.clicked.connect(self._on_send_clicked)
        input_layout.addWidget(send_btn)

        input_area.setLayout(input_layout)
        chat_layout.addWidget(input_area)

        chat_side.setLayout(chat_layout)
        main_layout.addWidget(chat_side, stretch=3)

        # ── Right: peer list panel ───────────────────────────
        self.peer_panel = QWidget()
        self.peer_panel.setFixedWidth(200)
        self.peer_panel.setStyleSheet(
            "background-color: #181825; border-left: 1px solid #313244;"
        )

        peer_panel_layout = QVBoxLayout()
        peer_panel_layout.setContentsMargins(0, 0, 0, 0)
        peer_panel_layout.setSpacing(0)

        panel_header = QLabel("  Peers")
        panel_header.setFixedHeight(56)
        panel_header.setFont(QFont("Arial", 13, QFont.Bold))
        panel_header.setStyleSheet("""
            color: #6c7086;
            background-color: #181825;
            border-bottom: 1px solid #313244;
            padding-left: 16px;
        """)
        peer_panel_layout.addWidget(panel_header)

        # Scroll area for peers
        peer_scroll = QScrollArea()
        peer_scroll.setWidgetResizable(True)
        peer_scroll.setStyleSheet("border: none; background-color: #181825;")

        self.peer_list_container = QWidget()
        self.peer_list_container.setStyleSheet("background-color: #181825;")
        self.peer_list_layout = QVBoxLayout()
        self.peer_list_layout.setAlignment(Qt.AlignTop)
        self.peer_list_layout.setContentsMargins(8, 8, 8, 8)
        self.peer_list_layout.setSpacing(6)
        self.peer_list_container.setLayout(self.peer_list_layout)

        peer_scroll.setWidget(self.peer_list_container)
        peer_panel_layout.addWidget(peer_scroll)

        self.peer_panel.setLayout(peer_panel_layout)
        main_layout.addWidget(self.peer_panel)

        self.setLayout(main_layout)

    def _on_send_clicked(self):
        text = self.text_input.text().strip()
        if text:
            self.on_send(text)
            self.text_input.clear()

    def _on_file_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select File", os.path.expanduser("~"), "All Files (*.*)"
        )
        if filepath:
            threading.Thread(
                target=self.on_send_file, args=(filepath,), daemon=True
            ).start()

    def add_message(
        self, from_name: str, text: str, timestamp: str, is_self: bool = False
    ):
        bubble = QWidget()
        bubble.setMaximumWidth(500)
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        name_label = QLabel(from_name)
        name_label.setStyleSheet(
            "color: #89b4fa; font-size: 12px; font-weight: bold; background: transparent;"
        )
        bubble_layout.addWidget(name_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            "color: #cdd6f4; font-size: 15px; background: transparent;"
        )
        bubble_layout.addWidget(text_label)

        time_label = QLabel(timestamp)
        time_label.setStyleSheet(
            "color: #6c7086; font-size: 11px; background: transparent;"
        )
        bubble_layout.addWidget(time_label)

        bubble.setLayout(bubble_layout)
        if is_self:
            bubble.setStyleSheet("background-color: #3b4261; border-radius: 12px;")
        else:
            bubble.setStyleSheet("background-color: #313244; border-radius: 12px;")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(bubble)
        row.addStretch()

        self.chat_layout.addLayout(row)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def add_peer(self, ip: str, name: str):
        """Adds a peer to the peer list panel."""
        if ip in self.peer_widgets:
            return

        peer_widget = QWidget()
        peer_widget.setStyleSheet("""
            QWidget {
                background-color: #313244;
                border-radius: 8px;
            }
        """)
        peer_layout = QVBoxLayout()
        peer_layout.setContentsMargins(10, 8, 10, 8)
        peer_layout.setSpacing(4)

        name_label = QLabel(f"👤 {name}")
        name_label.setStyleSheet(
            "color: #cdd6f4; font-size: 13px; font-weight: bold; background: transparent;"
        )
        peer_layout.addWidget(name_label)

        dm_btn = QPushButton("DM")
        dm_btn.setFixedHeight(28)
        dm_btn.setCursor(Qt.PointingHandCursor)
        dm_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #b4befe; }
        """)
        dm_btn.clicked.connect(lambda: self.on_dm(ip, name))
        peer_layout.addWidget(dm_btn)

        peer_widget.setLayout(peer_layout)
        self.peer_list_layout.addWidget(peer_widget)
        self.peer_widgets[ip] = peer_widget

    def remove_peer(self, ip: str):
        """Removes a peer from the peer list panel."""
        if ip in self.peer_widgets:
            widget = self.peer_widgets.pop(ip)
            self.peer_list_layout.removeWidget(widget)
            widget.deleteLater()

    def update_peers(self, count: int):
        self.peers_label.setText(f"● {count} peer{'s' if count != 1 else ''}")
        color = "#a6e3a1" if count > 0 else "#f38ba8"
        self.peers_label.setStyleSheet(f"color: {color};")

    def add_notification(self, text: str):
        """Shows a system message in chat like 'Arjun joined'."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #6c7086; font-size: 12px; padding: 4px;")
        self.chat_layout.addWidget(label)
