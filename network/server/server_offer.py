"""
UDP offer broadcaster for the server.

This module is responsible for:
- Creating a UDP broadcast socket
- Periodically sending offer messages that advertise the server
  name and TCP listening port

It does not handle TCP connections or game logic.
A main() function is intended for testing/debugging only.
"""


import socket
import time
import threading
from common.protocol import pack_offer, UDP_PORT_OFFER_LISTEN


def get_local_ip() -> str:
    """
    Best-effort way to figure out the local IP address (the one other machines can reach).
    It just asks the OS what source IP would be used.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        # Fallback
        return "127.0.0.1"
    finally:
        s.close()


def create_offer_socket() -> socket.socket:
    """
    Create a UDP socket configured for broadcast sending.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Allow quick restart
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s


def broadcast_offers(stop_event: threading.Event, server_name: str, tcp_port: int) -> None:
    """
    Broadcast UDP offer messages once per second until stop_event is set.
    """
    sock = create_offer_socket()
    try:
        while not stop_event.is_set():
            offer_bytes = pack_offer(tcp_port=tcp_port, server_name=server_name)
            sock.sendto(offer_bytes, ("<broadcast>", UDP_PORT_OFFER_LISTEN))
            time.sleep(1.0)
    finally:
        sock.close()

def main() -> None:
    tcp_port = 5000

    server_name = input("Enter server name (max 32 chars): ").strip() or "BlackjackServer"

    ip = get_local_ip()
    print(f"Server started, listening on IP address {ip}")
    print(f"Broadcasting offers on UDP port {UDP_PORT_OFFER_LISTEN} (TCP port in offer = {tcp_port})")

    sock = create_offer_socket()

    try:
        while True:
            offer_bytes = pack_offer(tcp_port=tcp_port, server_name=server_name)
            # Broadcast to the whole LAN on the hardcoded offer port
            sock.sendto(offer_bytes, ("<broadcast>", UDP_PORT_OFFER_LISTEN))
            time.sleep(1.0)  # not busy-waiting
    except KeyboardInterrupt:
        print("\nStopping server (Ctrl+C).")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
