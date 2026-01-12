"""
Client application entry point.

This module orchestrates the client lifecycle:
- Listens for UDP server offers
- Establishes a TCP connection to the server
- Initiates and delegates gameplay to the client session logic

"""


from session.client_session import run_client_session
from common.protocol import UDP_PORT_OFFER_LISTEN
from network.client.client_listener import create_listen_socket, wait_for_offer
from network.client.client_tcp import connect_and_send_request


def main() -> None:
    team_name = input("Enter team name (max 32 ASCII chars): ").strip() or "TeamClient"

    udp_sock = create_listen_socket()
    print(f"Client started, listening for offer requests on UDP port {UDP_PORT_OFFER_LISTEN}")

    try:
        while True:
            offer, server_ip = wait_for_offer(udp_sock)
            print(f"Received offer from {server_ip}, server name = {offer.server_name}, tcp port = {offer.tcp_port}")

            while True:
                rounds_str = input("Enter number of rounds (1-255): ").strip()
                try:
                    rounds = int(rounds_str)
                    if not (1 <= rounds <= 255):
                        raise ValueError()
                    break
                except ValueError:
                    print("Invalid rounds. Please enter an integer 1-255.")

            tcp_sock = None
            try:
                tcp_sock = connect_and_send_request(server_ip, offer.tcp_port, team_name, rounds)
                run_client_session(tcp_sock, rounds)
            except Exception as e:
                print(f"Failed to connect/run session with {offer.server_name}:{offer.tcp_port}: {e}")
            finally:
                if tcp_sock:
                    tcp_sock.close()

            print("Returning to listen for offers...\n")

    except KeyboardInterrupt:
        print("\nStopping client (Ctrl+C).")
    finally:
        udp_sock.close()



if __name__ == "__main__":
    main()
