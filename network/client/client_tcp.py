import socket
import sys

from common.protocol import pack_request


def main() -> None:
    # Allow running as: python -m client.client_tcp <server_ip> <tcp_port>
    if len(sys.argv) != 3:
        print("Usage: python -m client.client_tcp <server_ip> <tcp_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    tcp_port = int(sys.argv[2])

    team_name = input("Enter team name (max 32 ASCII chars): ").strip() or "TeamClient"
    rounds_str = input("Enter number of rounds (1-255): ").strip()
    rounds = int(rounds_str)

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


if __name__ == "__main__":
    main()
