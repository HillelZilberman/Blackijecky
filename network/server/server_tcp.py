"""
TCP infrastructure utilities for the server.

This module provides helper functions for:
- Creating and configuring a TCP listening socket
- Receiving fixed-length messages over TCP safely (recv_exact)

A main() function is intended for testing/debugging only.
"""


import socket
from typing import Tuple
from common.protocol import REQUEST_LEN, unpack_request


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """
    Receive exactly n bytes from a TCP socket.
    TCP is a stream, so one recv() may return less than requested.
    """
    chunks = []
    received = 0
    while received < n:
        chunk = sock.recv(n - received)
        if chunk == b"":
            # Connection closed unexpectedly
            raise ConnectionError("Socket closed while receiving data")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def create_tcp_listen_socket() -> Tuple[socket.socket, int]:
    """
    Create a TCP listening socket.
    Returns (socket, chosen_port).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to port 0 => OS chooses a free port
    s.bind(("", 0))
    port = s.getsockname()[1]

    s.listen()
    s.settimeout(1.0)
    return s, port


def main() -> None:
    server_sock, port = create_tcp_listen_socket()

    # Print the chosen TCP port
    print(f"TCP server listening on port {port}")

    try:
        while True:
            try:
                client_sock, (client_ip, client_port) = server_sock.accept()
            except socket.timeout:
                continue

            print(f"Accepted TCP connection from {client_ip}:{client_port}")

            try:
                # Read a full Request packet (fixed length by protocol)
                data = recv_exact(client_sock, REQUEST_LEN)
                req = unpack_request(data)

                print(
                    f"Received request: team={req.team_name}, rounds={req.rounds}"
                )

                # In the next step, the server will start the game rounds and exchange payloads.
                # For now, just close connection after handshake.
            except Exception as e:
                print(f"Error handling client {client_ip}:{client_port}: {e}")
            finally:
                client_sock.close()
                print(f"Closed connection to {client_ip}:{client_port}")

    except KeyboardInterrupt:
        print("\nStopping TCP server (Ctrl+C).")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
