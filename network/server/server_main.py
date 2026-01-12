"""
Server application entry point.

This module orchestrates the server lifecycle:
- Starts TCP and UDP networking components
- Accepts incoming client connections
- Delegates gameplay handling to the server session logic

"""


import socket
import threading
from common.protocol import REQUEST_LEN, unpack_request
from network.server.server_offer import get_local_ip, broadcast_offers
from network.server.server_tcp import create_tcp_listen_socket, recv_exact
from session.server_session import run_server_session


def main() -> None:
    server_name = input("Enter server name (max 32 chars): ").strip() or "BlackjackServer"

    # Start TCP server on an OS-chosen port
    server_sock, tcp_port = create_tcp_listen_socket()

    ip = get_local_ip()
    print(f"Server started, listening on IP address {ip}")
    print(f"Broadcasting offers on UDP port 13122 (TCP port in offer = {tcp_port})")

    # Start UDP offer broadcaster in a background thread
    stop_event = threading.Event()
    t = threading.Thread(
        target=broadcast_offers,
        args=(stop_event, server_name, tcp_port),
        daemon=True,
    )
    t.start()

    # Accept TCP clients forever
    try:
        while True:
            try:
                client_sock, (client_ip, client_port) = server_sock.accept()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                raise

            print(f"Accepted TCP connection from {client_ip}:{client_port}")

            try:
                data = recv_exact(client_sock, REQUEST_LEN)
                req = unpack_request(data)
                print(f"Received request: team={req.team_name}, rounds={req.rounds}")
                run_server_session(client_sock, req.team_name, req.rounds)
            except Exception as e:
                print(f"Error handling client {client_ip}:{client_port}: {e}")
            finally:
                client_sock.close()
                print(f"Closed connection to {client_ip}:{client_port}")

    except KeyboardInterrupt:
        print("\nStopping server (Ctrl+C).")
    finally:
        stop_event.set()
        server_sock.close()


if __name__ == "__main__":
    main()
