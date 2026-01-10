import socket
from typing import Tuple

from common.protocol import UDP_PORT_OFFER_LISTEN, ProtocolError, unpack_offer, pack_request


def create_listen_socket() -> socket.socket:
    """
    Create a UDP socket that listens for offer broadcasts on the hardcoded port 13122.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow running multiple clients on the same machine (useful for testing)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        # Some Windows builds don't support SO_REUSEPORT; ignore if unavailable.
        pass

    s.bind(("", UDP_PORT_OFFER_LISTEN))
    return s


def connect_and_send_request(server_ip: str, tcp_port: int, team_name: str, rounds: int) -> None:
    """
    Connect to the server via TCP and send a single Request message.
    """
    req_bytes = pack_request(rounds=rounds, team_name=team_name)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"Connecting to {server_ip}:{tcp_port} ...")
        sock.connect((server_ip, tcp_port))
        print("Connected. Sending request...")
        sock.sendall(req_bytes)
        print("Request sent. Closing connection.")
    finally:
        sock.close()


def main() -> None:
    team_name = input("Enter team name (max 32 ASCII chars): ").strip() or "TeamClient"

    sock = create_listen_socket()
    print(f"Client started, listening for offer requests on UDP port {UDP_PORT_OFFER_LISTEN}")

    try:
        while True:
            data, (server_ip, _) = sock.recvfrom(2048)

            # Ignore corrupted packets
            try:
                offer = unpack_offer(data)
            except ProtocolError:
                continue
            except Exception:
                continue

            print(f"Received offer from {server_ip}, server name = {offer.server_name}, tcp port = {offer.tcp_port}")

            # Ask user how many rounds to play (as in Example Run)
            while True:
                rounds_str = input("Enter number of rounds (1-255): ").strip()
                try:
                    rounds = int(rounds_str)
                    if not (1 <= rounds <= 255):
                        raise ValueError()
                    break
                except ValueError:
                    print("Invalid rounds. Please enter an integer 1-255.")

            # Use sender IP (server_ip) + offer tcp_port
            try:
                connect_and_send_request(server_ip, offer.tcp_port, team_name, rounds)
            except Exception as e:
                print(f"Failed to connect/send request to {server_ip}:{offer.tcp_port}: {e}")

            # After finishing, go back to listening (step 4 in example run)
            print("Returning to listen for offers...\n")

    except KeyboardInterrupt:
        print("\nStopping client (Ctrl+C).")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
