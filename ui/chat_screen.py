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


class ChatScreen(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, name: str, room_code: str, on_send, on_send_file):
        """
        name         → this peer's display name
        room_code    → current room code
        on_send      → callback fired with (text) when user sends a message
        on_send_file → callback fired with (filepath) when user sends a file
        """
        super().__init__()
        self.name = name
        self.room_code = room_code
        self.on_send = on_send
        self.on_send_file = on_send_file
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"LocalChat — Room {self.room_code}")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: #1e1e2e;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #313244; padding: 10px;")
        header_layout = QHBoxLayout()

        room_label = QLabel(f"Room: {self.room_code}")
        room_label.setFont(QFont("Arial", 12, QFont.Bold))
        room_label.setStyleSheet("color: #cdd6f4;")
        header_layout.addWidget(room_label)

        self.peers_label = QLabel("Peers: 0")
        self.peers_label.setStyleSheet("color: #6c7086;")
        self.peers_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.peers_label)

        header.setLayout(header_layout)
        layout.addWidget(header)

        # Chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # Input area
        input_area = QWidget()
        input_area.setStyleSheet("background-color: #313244;")
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(8)

        # File button
        file_btn = QPushButton("📎")
        file_btn.setFixedSize(40, 40)
        file_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        file_btn.clicked.connect(self._on_file_clicked)
        input_layout.addWidget(file_btn)

        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.text_input.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self.text_input)

        # Send button
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(80)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
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
        filepath, _ = QFileDialog.getOpenFileName(self, "Select File")
        if filepath:
            self.on_send_file(filepath)

    def add_message(
        self, from_name: str, text: str, timestamp: str, is_self: bool = False
    ):
        """Adds a message bubble to the chat."""
        bubble = QWidget()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(8, 6, 8, 6)

        name_label = QLabel(from_name)
        name_label.setStyleSheet("color: #89b4fa; font-size: 11px; font-weight: bold;")
        bubble_layout.addWidget(name_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #cdd6f4; font-size: 13px;")
        bubble_layout.addWidget(text_label)

        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #6c7086; font-size: 10px;")
        bubble_layout.addWidget(time_label)

        bubble.setLayout(bubble_layout)
        bubble.setStyleSheet("""
            background-color: #313244;
            border-radius: 10px;
        """)

        row = QHBoxLayout()
        if is_self:
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()

        self.chat_layout.addLayout(row)

        # Auto scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def update_peers(self, count: int):
        """Updates the peer count in the header."""
        self.peers_label.setText(f"Peers: {count}")
