# run_game.py
# Run from your project root:
#   python run_game.py

from game_engine.Round import Round, RoundState


def format_hand(hand, hide_second=False):
    """
    hand is a Hand object (your class stores cards in hand.hand list).
    hide_second=True will display the 2nd card as '?' (dealer hidden card).
    """
    cards = hand.hand  # list of Card objects
    parts = []
    for i, c in enumerate(cards):
        if hide_second and i == 1:
            parts.append("?")
        else:
            parts.append(str(c))
    return " ".join(parts)


def print_table(r: Round):
    # Hide dealer 2nd card only during player's turn
    hide_dealer = (r.state == RoundState.PLAYER_TURN)

    print("\n" + "-" * 40)
    print(f"Dealer: {format_hand(r.dealer_hand, hide_second=hide_dealer)}")
    if not hide_dealer:
        print(f"Dealer total: {r.dealer_hand.hand_sum()}")

    print(f"Player: {format_hand(r.player_hand)}")
    print(f"Player total: {r.player_hand.hand_sum()}")
    print("-" * 40)


def get_player_decision():
    """
    Returns exactly what your Round.apply_player_decision expects: "HIT" or "STAND".
    """
    while True:
        s = input("Hit or Stand? [h/s]: ").strip().lower()
        if s in ("h", "hit"):
            return "HIT"
        if s in ("s", "stand"):
            return "STAND"
        print("Please type 'h' for hit or 's' for stand.")


def main():
    r = Round()
    r.start()

    # Main round loop
    while r.state != RoundState.ROUND_OVER:
        print_table(r)

        # If player already busts, Round should end; this is just a safety check
        if r.player_hand.is_bust():
            break

        decision = get_player_decision()
        r.apply_player_decision(decision)

    # Final state
    print_table(r)
    print(f"\nROUND OVER. Outcome: {r.outcome}\n")


if __name__ == "__main__":
    main()
