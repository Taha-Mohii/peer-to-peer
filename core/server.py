import socket
import threading
from utils.framing import decode_message
from utils.crypto import decrypt_message

class Server:
    def __init__(self, host: str, port: int, key: bytes, on_message):
        """
        host       → IP to bind to, usually "0.0.0.0" (accept from anyone)
        port       → TCP port to listen on
        key        → AES key derived from room code
        on_message → callback fired when a message arrives
        """
        self.host = host
        self.port = port
        self.key = key
        self.on_message = on_message
        self.running = False
        
    def start(self):
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        print(f"[Server] Listening on {self.host}:{self.port}")

    def stop(self):
        self.running = False

    def _accept_loop(self):
        """Main loop __ accepts incoming connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(10)
            s.settimeout(1.0)
            
            while self.running:
                try:
                    conn, (ip, _) = s.accept()
                    threading.Thread(
                        target=self._handle_peer,
                        args = (conn,ip),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                
    def _handle_peer(self, conn: socket.socket, ip:str):
        """Handles all the messages from a single connected peer.""" 
        
        print(f"[Server] Connected: {ip}")
        with conn:
            while self.running:
                raw = decode_message(conn)
                if raw is None:
                    print(f"[Server] Disconnected: {ip}")
                    break
                
                
                encrypted = raw.get("payload")
                if not encrypted:
                    continue
                
                msg = decrypt_message(encrypted, self.key)
                if msg is None:
                    print("[Server] Bad decrypt from {ip} — ignored")
                    continue
                
                self.on_message(ip, msg)           