"""
session layer (client side).

This module drives the interactive client experience over a TCP socket.
It connects the protocol layer to a simple CLI "UI".

Responsibilities:
- For each round:
  * Receive server payloads (cards/results)
  * Display the current state
  * Ask the user for Hit/Stand when needed
  * Send decision payloads back to the server

Important:
- Protocol payloads do NOT specify "who received the card".
  We rely on the agreed ordering:
  * Round start: P1, D(up), P2
  * After HIT: one player card
  * After STAND: dealer hidden + dealer draws (0+), final payload carries final result
"""

from __future__ import annotations

import socket
from typing import List, Tuple

from common.protocol import (
    PAYLOAD_SERVER_LEN,
    RESULT_NOT_OVER,
    RESULT_TIE,
    RESULT_LOSS,
    RESULT_WIN,
    DECISION_HIT,
    DECISION_STAND,
    recv_exact,
    unpack_payload_server,
    pack_payload_decision,
)


# Protocol suit encoding order is HDCS: 0=H, 1=D, 2=C, 3=S
_PROTO_SUIT_TO_SYMBOL = {
    0: "♥",
    1: "♦",
    2: "♣",
    3: "♠",
}

_RANK_TO_STR = {
    1: "A",
    11: "J",
    12: "Q",
    13: "K",
}

def _format_card(rank: int, suit: int) -> str:
    return f"{_RANK_TO_STR.get(rank, str(rank))}{_PROTO_SUIT_TO_SYMBOL.get(suit, str(suit))}"

def _hand_sum(ranks: List[int]) -> int:
    """
    Blackjack sum (same logic as your Hand.hand_sum):
    - Face cards count as 10
    - Ace counts as 11, but can drop to 1 if bust
    """
    total = 0
    aces = 0
    for r in ranks:
        if r == 1:
            aces += 1
            total += 11
        elif r >= 11:
            total += 10
        else:
            total += r
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def _result_to_text(code: int) -> str:
    if code == RESULT_WIN:
        return "WIN"
    if code == RESULT_LOSS:
        return "LOSS"
    if code == RESULT_TIE:
        return "TIE"
    return "NOT_OVER"


def _print_state(player_cards: List[str], dealer_cards: List[str], player_ranks: List[int], dealer_ranks: List[int], hide_dealer_second: bool) -> None:
    print("\n--- Current Table ---")
    print("Player:")
    print("  " + ", ".join(player_cards))
    hand_sum = _hand_sum(player_ranks)
    print(f"  Sum = {hand_sum}")

    print("Dealer:")
    if hide_dealer_second and len(dealer_cards) >= 2:
        shown = [dealer_cards[0], "??"]
        print("  " + ", ".join(shown))
        # Don't show dealer sum when hidden
    else:
        print("  " + ", ".join(dealer_cards))
        print(f"  Sum = {_hand_sum(dealer_ranks)}")
    print("---------------------\n")


def run_client_session(tcp_sock: socket.socket, rounds: int) -> None:
    """
    Run an interactive client session for a fixed number of rounds.

    Args:
        tcp_sock: connected TCP socket
        rounds: number of rounds to play
    """
    wins = 0
    played = 0
    for r in range(1, rounds + 1):
        print(f"\n====================")
        print(f"Round {r}/{rounds}")
        print(f"====================")

        player_cards: List[str] = []
        dealer_cards: List[str] = []
        player_ranks: List[int] = []
        dealer_ranks: List[int] = []

        # ---- Initial 3 payloads: P1, D(up), P2
        for i in range(3):
            pkt = recv_exact(tcp_sock, PAYLOAD_SERVER_LEN)
            payload = unpack_payload_server(pkt)
            card_str = _format_card(payload.rank, payload.suit)

            if i in (0, 2):  # player cards
                player_cards.append(card_str)
                player_ranks.append(payload.rank)
            else:  # i == 1 dealer up-card
                dealer_cards.append(card_str)
                dealer_ranks.append(payload.rank)

            # If server ended immediately (rare), handle it.
            if payload.result != RESULT_NOT_OVER:
                _print_state(player_cards, dealer_cards, player_ranks, dealer_ranks, hide_dealer_second=True)
                print(f"Result: {_result_to_text(payload.result)}")
                played += 1
                if payload.result == RESULT_WIN:
                    wins += 1
                break
        else:
            # Only if we didn't break early
            _print_state(player_cards, dealer_cards, player_ranks, dealer_ranks, hide_dealer_second=True)

            # ---- Player turn loop
            while True:
                # Ask for decision
                choice = input("Your move [h=hit / s=stand]: ").strip().lower()
                if choice in ("h", "hit"):
                    tcp_sock.sendall(pack_payload_decision(DECISION_HIT))

                    # Receive exactly one card update (player hit)
                    pkt = recv_exact(tcp_sock, PAYLOAD_SERVER_LEN)
                    payload = unpack_payload_server(pkt)
                    card_str = _format_card(payload.rank, payload.suit)

                    player_cards.append(card_str)
                    player_ranks.append(payload.rank)

                    _print_state(player_cards, dealer_cards, player_ranks, dealer_ranks, hide_dealer_second=True)

                    if payload.result != RESULT_NOT_OVER:
                        print(f"Result: {_result_to_text(payload.result)}")
                        played += 1
                        if payload.result == RESULT_WIN:
                            wins += 1

                        break

                elif choice in ("s", "stand"):
                    tcp_sock.sendall(pack_payload_decision(DECISION_STAND))

                    # After stand, server will send dealer hidden card + possibly more draws.
                    hide_dealer_second = False
                    while True:
                        pkt = recv_exact(tcp_sock, PAYLOAD_SERVER_LEN)
                        payload = unpack_payload_server(pkt)
                        card_str = _format_card(payload.rank, payload.suit)

                        dealer_cards.append(card_str)
                        dealer_ranks.append(payload.rank)

                        _print_state(player_cards, dealer_cards, player_ranks, dealer_ranks, hide_dealer_second=False)

                        if payload.result != RESULT_NOT_OVER:
                            print(f"Result: {_result_to_text(payload.result)}")
                            played += 1
                            if payload.result == RESULT_WIN:
                                wins += 1

                            break
                    break
                else:
                    print("Invalid input. Type 'h' or 's'.")

        win_rate = (wins / played) if played > 0 else 0.0
        print(f"Finished playing {played} rounds, win rate: {win_rate:.2%}")
        print("\n(End of round)\n")
