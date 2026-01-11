import socket
from typing import Tuple

from common import protocol
from game_engine.Round import Round, RoundState


# --- Helpers: TCP recv exact (stream-safe) ---
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


# --- Helpers: card conversion from engine -> protocol fields ---
def card_to_rank_suit(card) -> Tuple[int, int]:
    """
    Convert a Card object from your engine into (rank, suit) ints expected by the protocol.
    Tries common attribute names safely.
    """
    # rank
    for attr in ("rank", "value", "number"):
        if hasattr(card, attr):
            rank = int(getattr(card, attr))
            break
    else:
        raise AttributeError("Card object missing rank/value/number attribute")

    # suit
    if hasattr(card, "suit"):
        suit_val = getattr(card, "suit")
        suit = int(suit_val)  # if suit is enum-like this still works
    else:
        raise AttributeError("Card object missing suit attribute")

    return rank, suit


def outcome_to_result_byte(outcome: str) -> int:
    """
    Map engine outcome string to protocol result byte:
      1=tie, 2=loss, 3=win
    """
    if outcome in ("WIN", "BLACKJACK"):
        return 3
    if outcome == "LOSS":
        return 2
    if outcome == "TIE":
        return 1
    raise ValueError(f"Unknown outcome: {outcome}")


def send_server_payload(sock: socket.socket, result: int, rank: int, suit: int) -> None:
    """
    Wrapper around protocol packer.
    IMPORTANT: protocol always includes 3 bytes for card; client ignores card when result != 0.
    """
    pkt = protocol.pack_payload_server(result=result, rank=rank, suit=suit)
    sock.sendall(pkt)


def run_server_session(conn: socket.socket, team_name: str, rounds: int) -> None:
    """
    Run one full session for a single TCP client (after REQUEST is received).
    Prints stages of the game for this connection.
    """
    print(f"[SESSION] Starting session for team='{team_name}', rounds={rounds}")

    # Dummy card to attach to "result-only" payloads (protocol always needs a card)
    DUMMY_RANK, DUMMY_SUIT = 1, 0  # Ace of suit 0; client must ignore when result!=0

    for r_index in range(1, rounds + 1):
        rnd = Round()
        rnd.start()

        print(f"\n[ROUND {r_index}/{rounds}] Initial deal")

        # After start(): assume 2 cards to player, 2 to dealer exist in hands
        player_cards = rnd.player_hand.hand
        dealer_cards = rnd.dealer_hand.hand

        # Track how many cards already announced to client
        sent_player = 0
        sent_dealer = 0

        # Send player's first two cards
        for _ in range(2):
            c = player_cards[sent_player]
            rank, suit = card_to_rank_suit(c)
            send_server_payload(conn, result=0, rank=rank, suit=suit)
            print(f"[SERVER->CLIENT] Player card: {c}")
            sent_player += 1

        # Send dealer upcard only (index 0)
        up = dealer_cards[0]
        rank, suit = card_to_rank_suit(up)
        send_server_payload(conn, result=0, rank=rank, suit=suit)
        print(f"[SERVER->CLIENT] Dealer upcard: {up}")
        sent_dealer = 1  # hidden (index 1) not sent yet

        # --- Player turn loop ---
        while rnd.state == RoundState.PLAYER_TURN:
            print("[SERVER] Waiting for player decision (Hittt/Stand)")

            decision_bytes = recv_exact(conn, protocol.PAYLOAD_CLIENT_LEN)
            decision = protocol.unpack_payload_decision(decision_bytes)

            print(f"[CLIENT->SERVER] Decision: {decision}")

            if decision == "Hittt":
                rnd.apply_player_decision("HIT")
            elif decision == "Stand":
                rnd.apply_player_decision("STAND")
            else:
                # protocol already validates, but keep safe
                raise ValueError(f"Unexpected decision: {decision}")

            # If engine added new player cards, send them
            while len(rnd.player_hand.hand) > sent_player:
                c = rnd.player_hand.hand[sent_player]
                rank, suit = card_to_rank_suit(c)
                send_server_payload(conn, result=0, rank=rank, suit=suit)
                print(f"[SERVER->CLIENT] Player drew: {c}")
                sent_player += 1

            # If round ended due to bust, send final result
            if rnd.state == RoundState.ROUND_OVER:
                res = outcome_to_result_byte(rnd.outcome)
                send_server_payload(conn, result=res, rank=DUMMY_RANK, suit=DUMMY_SUIT)
                print(f"[SERVER->CLIENT] Round over (player phase). Outcome={rnd.outcome}")
                break

        # --- Dealer turn + finish (only if not already over) ---
        if rnd.state != RoundState.ROUND_OVER:
            print("[ROUND] Dealer reveal + dealer play")

            # Reveal dealer hidden card (index 1) once player turn ended
            while len(rnd.dealer_hand.hand) > sent_dealer:
                c = rnd.dealer_hand.hand[sent_dealer]
                rank, suit = card_to_rank_suit(c)
                send_server_payload(conn, result=0, rank=rank, suit=suit)
                print(f"[SERVER->CLIENT] Dealer reveal/draw: {c}")
                sent_dealer += 1

            # Some engines will keep drawing dealer cards internally after STAND.
            # Ensure we announce any extra dealer cards that appear until ROUND_OVER.
            while rnd.state != RoundState.ROUND_OVER:
                # If your Round requires an explicit step for dealer, add it here.
                # Many engines already finish dealer logic inside apply_player_decision("STAND").
                # We'll just break to avoid spinning.
                break

            # After dealer done, announce any newly added dealer cards
            while len(rnd.dealer_hand.hand) > sent_dealer:
                c = rnd.dealer_hand.hand[sent_dealer]
                rank, suit = card_to_rank_suit(c)
                send_server_payload(conn, result=0, rank=rank, suit=suit)
                print(f"[SERVER->CLIENT] Dealer draw: {c}")
                sent_dealer += 1

            # Final result
            res = outcome_to_result_byte(rnd.outcome)
            send_server_payload(conn, result=res, rank=DUMMY_RANK, suit=DUMMY_SUIT)
            print(f"[SERVER->CLIENT] Round over. Outcome={rnd.outcome}")

    print(f"\n[SESSION] Finished session for team='{team_name}'. Closing session.")
