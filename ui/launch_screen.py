from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LaunchScreen(QWidget):
    def __init__(self, on_join):
        """on_join -> callback fired with (name, room_code) where user clicks join."""

        super().__init__()
        self.on_join = on_join
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("LocalChat")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #1e1e2e;")

        layout = QVBoxLayout()
        layout.setContentsMargins(40,40,40,40)
        layout.setSpacing(20)
        title = QLabel("LocalChat")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #cdd6f4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Offline P2P Chat & File Sharing")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: #6c7086;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.name_input)

        # Room code input
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Room code (e.g. 482901)")
        self.room_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.room_input)

        # Join button
        join_btn = QPushButton("Join Room")
        join_btn.setStyleSheet("""
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
        join_btn.clicked.connect(self._on_join_clicked)
        layout.addWidget(join_btn)

        self.setLayout(layout)


        def _on_join_clicked(self):
            name = self.name_input.text().strip()
            room = self.room_input.text().strip()
            
            
            if not name:
                QMessageBox.warning(self, "Error", "Please enter your name.")
                return
            
            if not room:
                QMessageBox.warning(self, "Error" , "Please enter a room code.")
                return
            
            self.on_join(name, room)