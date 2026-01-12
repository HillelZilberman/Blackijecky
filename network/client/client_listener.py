"""
UDP offer listener for the client.

This module is responsible for:
- Creating a UDP socket bound to the offer listening port
- Receiving and validating server offer messages
- Filtering out corrupted or irrelevant packets

It performs only server discovery (UDP) and does not handle
TCP connections or game logic.

A main() function is intended for testing/debugging only.
"""


import socket
from common.protocol import UDP_PORT_OFFER_LISTEN, unpack_offer, ProtocolError


def create_listen_socket() -> socket.socket:
    """
    Create and bind a UDP socket for listening to server offer broadcasts.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass
    s.bind(("", UDP_PORT_OFFER_LISTEN))
    s.settimeout(1.0)
    return s


def wait_for_offer(sock: socket.socket):
    """
    Block until a valid server offer is received and return the offer and server IP.
    """
    while True:
        try:
            data, (server_ip, _) = sock.recvfrom(2048)
        except socket.timeout:
            continue
        try:
            offer = unpack_offer(data)
            return offer, server_ip
        except ProtocolError:
            continue
        except Exception:
            continue


def main() -> None:
    print(f"Client started, listening for offer requests on UDP port {UDP_PORT_OFFER_LISTEN}")

    sock = create_listen_socket()
    try:
        while True:
            data, (src_ip, src_port) = sock.recvfrom(2048)  # blocking, no busy-wait
            try:
                offer = unpack_offer(data)
            except Exception:
                # Ignore corrupted/unknown packets as required by guidelines
                continue

            print(
                f"Received offer from {src_ip}, "
                f"server name = {offer.server_name}, "
                f"tcp port = {offer.tcp_port}"
            )

    except KeyboardInterrupt:
        print("\nStopping client (Ctrl+C).")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
