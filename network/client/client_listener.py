import socket

from common.protocol import UDP_PORT_OFFER_LISTEN, unpack_offer


def create_listen_socket() -> socket.socket:
    """
    Create a UDP socket bound to the hardcoded offer port (13122).
    SO_REUSEPORT is enabled to allow multiple clients on the same machine.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow quick restart
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Allow multiple clients on same computer to bind same UDP port (if supported)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            # Some Windows builds may not allow it even if present
            pass

    s.bind(("", UDP_PORT_OFFER_LISTEN))
    return s


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
