import threading

class Election:
    def __init__(self, device_id: str, peer_manager, client, on_elected):
        """
        device_id   → this peer's unique ID (from config)
        peer_manager → PeerManager instance
        client      → Client instance for sending messages
        on_elected  → callback fired when this peer becomes host
        """
        self.device_id = device_id
        self.peer_manager = peer_manager
        self.client = client
        self.on_elected = on_elected
        self.is_host = False
        self._lock = threading.Lock()

    def run(self):
        """
        Compare our device_id against all known peers.
        Highest ID wins and becomes host.
        """

        peers = self.peer_manager.get_peers()

        # If no peers, we are automatically host
        if not peers:
            self._become_host()
            return

        # Check if our ID is highest
        all_ids = list(peers.keys()) + [self.device_id]
        if max(all_ids) == self.device_id:
            self._become_host()

    def _become_host(self):
        with self._lock:
            if not self.is_host:
                self.is_host = True
                print("[Election] This peer is now the HOST")
                self.on_elected()

    def is_current_host(self)-> bool:
        return self.is_host

    def reset(self):
        """Called when host leaves — trigger re-election."""

        with self._lock:
            self.is_host = False
        print("[Election] Host left — re-running election")
        self.run()
