from GameEngine.Round import Round, RoundState

PAYOUT = {"WIN": 2, "BLACKJACK": 2.5, "LOSS": 0, "TIE": 1}

class GameSession:
    def __init__(self, num_rounds):
        self.num_rounds = num_rounds
        self.bet_per_round = 10
        self.balance = num_rounds * self.bet_per_round
        self.current_round = None
        self.round_counter = 0

        # Session stats:
        self.wins = 0
        self.losses = 0
        self.ties = 0


    def start_next_round(self):
        if self.is_over():
            return None

        self.round_counter += 1
        self.balance -= self.bet_per_round

        round = Round()
        round.start()
        self.current_round = round
        return round


    def is_over(self):
        return self.round_counter >= self.num_rounds or self.balance < self.bet_per_round

    def record_outcome(self, outcome):
        if outcome in ("BLACKJACK", "WIN"):
            self.wins += 1
        elif outcome == "LOSS":
            self.losses += 1
        elif outcome == "TIE":
            self.ties += 1
        else:
            raise ValueError(f"Unknown outcome: {outcome}")

        self.balance += self.bet_per_round * PAYOUT[outcome]









