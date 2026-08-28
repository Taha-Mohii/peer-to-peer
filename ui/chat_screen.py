from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import threading
import os

class ChatScreen(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, name: str, room_code: str, on_send, on_send_file):
        super().__init__()
        self.name = name
        self.room_code = room_code
        self.on_send = on_send
        self.on_send_file = on_send_file
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"LocalChat — Room {self.room_code}")
        self.setMinimumSize(700, 550)
        self.setStyleSheet("background-color: #89b4fa;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────
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
        layout.addWidget(header)

        # ── Chat area ────────────────────────────────────────
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
        layout.addWidget(self.scroll_area)

        # ── Input area ───────────────────────────────────────
        input_area = QWidget()
        input_area.setFixedHeight(72)
        input_area.setStyleSheet(
            "background-color: #181825; border-top: 1px solid #313244;"
        )
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        # File button
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

        # Text input
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

        # Send button
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
        layout.addWidget(input_area)

        self.setLayout(layout)

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
                target=self.on_send_file,
                args=(filepath,),
                daemon=True
            ).start()

    def add_message(
        self, from_name: str, text: str, timestamp: str, is_self: bool = False
    ):
        """Adds a message bubble to the chat."""
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
        if is_self:
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        self.chat_layout.addLayout(row)

        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def update_peers(self, count: int):
        """Updates the peer count in the header."""
        self.peers_label.setText(f"● {count} peer{'s' if count != 1 else ''}")
        color = "#a6e3a1" if count > 0 else "#f38ba8"
        self.peers_label.setStyleSheet(f"color: {color};")
