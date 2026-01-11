import socket

from common import protocol


def recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    received = 0
    while received < n:
        chunk = sock.recv(n - received)
        if chunk == b"":
            raise ConnectionError("Socket closed while receiving data")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def result_to_text(result: int) -> str:
    return {0: "ROUND_IS_NOT_OVER", 1: "TIE", 2: "LOSS", 3: "WIN"}.get(result, f"UNKNOWN({result})")


def prompt_decision() -> str:
    while True:
        s = input("Hit or Stand? [h/s]: ").strip().lower()
        if s in ("h", "hit"):
            return "Hittt"
        if s in ("s", "stand"):
            return "Stand"
        print("Please type 'h' for hit or 's' for stand.")


def run_client_session(conn: socket.socket, rounds: int) -> None:
    """
    Run the client-side logic on an open TCP connection AFTER sending REQUEST.
    """
    wins = losses = ties = 0

    payload_len = protocol.PAYLOAD_SERVER_LEN
    decision_len = protocol.DECISION_LEN

    print(f"[SESSION] Connected to server. Playing {rounds} rounds...")

    for r_index in range(1, rounds + 1):
        print(f"\n[ROUND {r_index}/{rounds}] Waiting for initial deal...")

        # Initial 3 payloads: player1, player2, dealer_upcard
        for i in range(3):
            pkt = recv_exact(conn, payload_len)
            msg = protocol.unpack_payload_server(pkt)
            print(f"[SERVER->CLIENT] result={result_to_text(msg.result)}, card=(rank={msg.rank}, suit={msg.suit})")

        # Player turn: keep choosing until stand or server ends round
        while True:
            decision = prompt_decision()
            conn.sendall(protocol.pack_payload_decision(decision))
            print(f"[CLIENT->SERVER] Decision sent: {decision}")

            pkt = recv_exact(conn, payload_len)
            msg = protocol.unpack_payload_server(pkt)

            if msg.result == 0:
                # hit card or dealer reveal/draw depending on timing; print anyway
                print(f"[SERVER->CLIENT] card update: (rank={msg.rank}, suit={msg.suit})")
                if decision == "Stand":
                    # after stand, we should just keep reading until result != 0
                    break
                continue

            # round ended immediately (e.g., player bust)
            outcome = result_to_text(msg.result)
            print(f"[SERVER->CLIENT] ROUND OVER: {outcome}")
            if msg.result == 3:
                wins += 1
            elif msg.result == 2:
                losses += 1
            elif msg.result == 1:
                ties += 1
            break

        # If we stood, server will now send dealer cards (result=0) until final result !=0
        if msg.result == 0:
            while True:
                pkt = recv_exact(conn, payload_len)
                msg = protocol.unpack_payload_server(pkt)

                if msg.result == 0:
                    print(f"[SERVER->CLIENT] dealer card: (rank={msg.rank}, suit={msg.suit})")
                    continue

                outcome = result_to_text(msg.result)
                print(f"[SERVER->CLIENT] ROUND OVER: {outcome}")
                if msg.result == 3:
                    wins += 1
                elif msg.result == 2:
                    losses += 1
                elif msg.result == 1:
                    ties += 1
                break

    total = wins + losses + ties
    win_rate = (wins / total) if total else 0.0
    print(f"\n[SESSION] Finished playing {total} rounds. wins={wins}, losses={losses}, ties={ties}, win_rate={win_rate:.2%}")
