from game_engine.Round import Round, RoundState

class GameSession:
    def __init__(self, num_rounds):
        self.num_rounds = num_rounds
        self.current_round = None
        self.round_counter = 0

        # session stats:
        self.wins = 0
        self.losses = 0
        self.ties = 0


    def start_next_round(self):
        if self.is_over():
            return None

        self.round_counter += 1

        round = Round()
        round.start()
        self.current_round = round
        return round


    def is_over(self):
        return self.round_counter >= self.num_rounds

    def record_outcome(self, outcome):
        if outcome in ("BLACKJACK", "WIN"):
            self.wins += 1
        elif outcome == "LOSS":
            self.losses += 1
        elif outcome == "TIE":
            self.ties += 1
        else:
            raise ValueError(f"Unknown outcome: {outcome}")










