# RunGame.py
# Run from project root:
#   python RunGame.py


from game_engine.Round import RoundState
from session.game_session import GameSession




def format_hand(hand, hide_second=False):
    """
    Your Hand stores cards in hand.hand (list of Card objects).
    hide_second=True prints '?' instead of the 2nd card.
    """
    cards = hand.hand
    parts = []
    for i, c in enumerate(cards):
        if hide_second and i == 1:
            parts.append("?")
        else:
            parts.append(str(c))
    return " ".join(parts)


def print_table(r):
    hide_dealer = (r.state == RoundState.PLAYER_TURN)

    print("\n" + "-" * 42)
    print(f"Dealer: {format_hand(r.dealer_hand, hide_second=hide_dealer)}")
    if not hide_dealer:
        print(f"Dealer total: {r.dealer_hand.hand_sum()}")

    print(f"Player: {format_hand(r.player_hand)}")
    print(f"Player total: {r.player_hand.hand_sum()}")
    print("-" * 42)


def get_player_decision():
    while True:
        s = input("Hit or Stand? [h/s]: ").strip().lower()
        if s in ("h", "hit"):
            return "HIT"
        if s in ("s", "stand"):
            return "STAND"
        print("Please type 'h' for hit or 's' for stand.")


def play_round(r):
    """Plays one Round until it's over (CLI decisions)."""
    while r.state != RoundState.ROUND_OVER:
        print_table(r)

        # safety check (Round should set outcome/state on bust)
        if r.player_hand.is_bust():
            break

        decision = get_player_decision()
        r.apply_player_decision(decision)

    # final reveal
    print_table(r)
    print(f"ROUND OVER. Outcome: {r.outcome}\n")


def read_positive_int(prompt):
    while True:
        try:
            x = int(input(prompt).strip())
            if x <= 0:
                print("Please enter a positive number.")
                continue
            return x
        except ValueError:
            print("Please enter a valid integer.")


def main():
    num_rounds = read_positive_int("How many rounds do you want to play? ")

    session = GameSession(num_rounds)
    starting_balance = session.balance  # should be num_rounds * 10 after your change

    print("\n=== SESSION START ===")
    print(f"Rounds: {session.num_rounds}")
    print(f"Bet per round: {session.bet_per_round}")
    print(f"Starting chips: {starting_balance}\n")

    while True:
        r = session.start_next_round()
        if r is None:
            break

        print(f"=== ROUND {session.round_counter}/{session.num_rounds} ===")
        print(f"Chips before playing this round: {session.balance}")
        play_round(r)

        # Update session stats + chips payout based on outcome
        session.record_outcome(r.outcome)

        print(f"Chips after this round: {session.balance}\n")

    # Summary
    final_balance = session.balance
    profit = final_balance - starting_balance

    print("=== SESSION SUMMARY ===")
    print(f"Rounds played: {session.round_counter}/{session.num_rounds}")
    print(f"Wins:   {session.wins}")
    print(f"Losses: {session.losses}")
    print(f"Ties:   {session.ties}")
    print(f"Starting chips: {starting_balance}")
    print(f"Final chips:    {final_balance}")
    print(f"Profit:         {profit:+d}")


if __name__ == "__main__":
    main()
