"""
session layer (server side).

This module is the "gameplay director" for a single TCP-connected client.
It connects the networking/protocol layer to the pure game-engine layer.

Responsibilities:
- Drive N blackjack rounds using the game engine (GameSession/Round)
- Receive client decisions (Hittt/Stand) via TCP payloads
- Send server payloads that reveal cards + round result updates

Notes:
- The underlying protocol payload does NOT include "who received the card".
  Therefore, we rely on ordering:
  * At round start: server sends 3 cards in order: player, dealer(up), player
  * After a HIT decision: server sends 1 player card
  * After a STAND decision: server sends dealer hidden card, then dealer draws (0+),
    with the FINAL payload carrying the final result code.
"""

from __future__ import annotations

import socket
from typing import Optional, Tuple, List

from common.protocol import (
    PAYLOAD_CLIENT_LEN,
    RESULT_NOT_OVER,
    RESULT_TIE,
    RESULT_LOSS,
    RESULT_WIN,
    DECISION_HIT,
    DECISION_STAND,
    recv_exact,
    unpack_payload_decision,
    pack_payload_server,
)

from session.game_session import GameSession


# -------------------------
# Suit mapping
# -------------------------
# Your Card uses: 0=♠, 1=♥, 2=♦, 3=♣  (see Card.SUIT_TO_STR)
# The protocol uses: 0=H, 1=D, 2=C, 3=S  (see protocol.py)
_INTERNAL_TO_PROTO_SUIT = {
    1: 0,  # ♥ -> H
    2: 1,  # ♦ -> D
    3: 2,  # ♣ -> C
    0: 3,  # ♠ -> S
}

def _to_proto_rank_suit(card) -> Tuple[int, int]:
    """
    Convert a game-engine Card to (rank, suit) as expected by the protocol.
    """
    rank = int(card.rank)
    suit_internal = int(card.suit)
    suit_proto = _INTERNAL_TO_PROTO_SUIT.get(suit_internal)
    if suit_proto is None:
        raise ValueError(f"Unknown internal suit: {suit_internal}")
    return rank, suit_proto


def _outcome_to_result_code(outcome: Optional[str]) -> int:
    """
    Map game-engine outcome string to protocol result code.
    """
    if outcome is None:
        return RESULT_NOT_OVER
    if outcome == "WIN" or outcome == "BLACKJACK":
        return RESULT_WIN
    if outcome == "LOSS":
        return RESULT_LOSS
    if outcome == "TIE":
        return RESULT_TIE
    # Fallback: treat unknown as not-over (safer than crashing the whole server)
    return RESULT_NOT_OVER


def _send_card(sock: socket.socket, card, result_code: int) -> None:
    """
    Send a single Server Payload containing (result, card).
    """
    rank, suit = _to_proto_rank_suit(card)
    pkt = pack_payload_server(result=result_code, rank=rank, suit=suit)
    sock.sendall(pkt)

def handle_stand_and_send_dealer(
    client_sock,
    rnd,
    sent_dealer
):
    """
    Handle STAND decision:
    - Let dealer play
    - Send all unseen dealer cards to client
    - Attach outcome to the last sent card
    - Return updated sent_dealer
    """

    # Dealer plays (reveal hidden card + draw until 17+)
    before_d = len(rnd.dealer_hand.hand)
    rnd.apply_player_decision("STAND")
    after_d = len(rnd.dealer_hand.hand)

    # Cards the client has not seen yet
    new_cards = rnd.dealer_hand.hand[sent_dealer:after_d]
    if not new_cards and after_d > 0:
        # Defensive fallback if sent_dealer is wrong
        new_cards = rnd.dealer_hand.hand[1:after_d]

    # Send dealer cards; last one carries the outcome
    for i, c in enumerate(new_cards):
        is_last = (i == len(new_cards) - 1)
        if is_last and rnd.outcome in ("WIN", "LOSS", "TIE", "BLACKJACK"):
            result_code = _outcome_to_result_code(rnd.outcome)
        else:
            result_code = RESULT_NOT_OVER
        _send_card(client_sock, c, result_code)

    sent_dealer = after_d

    # Edge case: no new cards were sent, but outcome exists
    if rnd.outcome in ("WIN", "LOSS", "TIE", "BLACKJACK") and len(new_cards) == 0:
        ref_card = rnd.dealer_hand.hand[-1] if rnd.dealer_hand.hand else rnd.player_hand.hand[-1]
        _send_card(client_sock, ref_card, _outcome_to_result_code(rnd.outcome))

    return sent_dealer



def run_server_session(client_sock: socket.socket, team_name: str, rounds: int) -> None:
    """
    Run a full game session for one connected client.

    Args:
        client_sock: connected TCP socket
        team_name: client team name (for logs)
        rounds: number of rounds requested
    """
    session = GameSession(rounds)

    print(f"[SESSION] Starting session for team={team_name!r}, rounds={rounds}")

    for round_index in range(rounds):
        rnd = session.start_next_round()
        if rnd is None:
            print("[SESSION] session ended early (no more balance or rounds).")
            break

        # ---- Round start: deal already happened inside GameSession.start_next_round() -> Round.start()
        # Send visible cards in the required order:
        #   P1, D(up), P2
        player_cards = rnd.player_hand.hand
        dealer_cards = rnd.dealer_hand.hand

        if len(player_cards) < 2 or len(dealer_cards) < 2:
            raise RuntimeError("Round did not deal expected 2 cards each")

        # Track how many cards were already sent to the client (by hand)
        sent_player = 0
        sent_dealer = 0

        # Send P1
        _send_card(client_sock, player_cards[0], RESULT_NOT_OVER)
        sent_player = 1

        # Send D up-card (dealer_cards[0])
        _send_card(client_sock, dealer_cards[0], RESULT_NOT_OVER)
        sent_dealer = 1

        # Send P2
        # If blackjack, mark the 3rd payload as final
        if rnd.player_hand.hand_sum() == 21:
            rnd.outcome = "BLACKJACK"
            _send_card(client_sock, player_cards[1], RESULT_WIN)  # <-- פה השינוי
            session.record_outcome("BLACKJACK")
            print(f"[ROUND {round_index + 1}] BLACKJACK -> WIN")
            continue
        else:
            _send_card(client_sock, player_cards[1], RESULT_NOT_OVER)
            sent_player = 2

        # ---- Player decision loop
        while True:
            # If round already ended (bust or dealer finished), stop.
            if rnd.outcome in ("WIN", "LOSS", "TIE", "BLACKJACK"):
                break

            if rnd.need_player_decision():
                # Read client decision payload
                decision_pkt = recv_exact(client_sock, PAYLOAD_CLIENT_LEN)
                decision = unpack_payload_decision(decision_pkt)

                if decision == DECISION_HIT:
                    before_p = len(rnd.player_hand.hand)
                    rnd.apply_player_decision("HIT")
                    after_p = len(rnd.player_hand.hand)

                    # Send any newly drawn player cards (should be 1)
                    if after_p > before_p:
                        for c in rnd.player_hand.hand[before_p:after_p]:
                            result_code = _outcome_to_result_code(rnd.outcome)
                            _send_card(client_sock, c, result_code)

                    # If player busted, outcome is LOSS and we already sent final LOSS with the bust card.
                    if rnd.outcome in ("WIN", "LOSS", "TIE", "BLACKJACK"):
                        break

                elif decision == DECISION_STAND:
                    sent_dealer = handle_stand_and_send_dealer(client_sock, rnd, sent_dealer);
                else:
                    # Unknown decision - treat as stand for safety
                    print(f"[WARN] Unknown decision={decision}. Treating as STAND.")
                    sent_dealer = handle_stand_and_send_dealer(client_sock, rnd, sent_dealer)
                    break
            else:
                # No player decision needed; if this happens, we assume round is over.
                break

        # ---- Record outcome (if any)
        if rnd.outcome in ("WIN", "LOSS", "TIE", "BLACKJACK"):
            session.record_outcome(rnd.outcome)
            print(f"[ROUND {round_index+1}] outcome={rnd.outcome}")

    print(
        f"[SESSION] Done. stats: wins={session.wins}, losses={session.losses}, ties={session.ties} "
    )
