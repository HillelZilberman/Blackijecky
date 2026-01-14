from game_engine.Round import Round, RoundState


class GameSession:
    """
    Manages a multi-round Blackjack game session.

    Responsibilities:
    - Track how many rounds should be played
    - Start new rounds one by one
    - Count wins, losses, and ties across the session
    """

    def __init__(self, num_rounds):
        """
        Create a new game session.

        Args:
            num_rounds (int): Total number of rounds to play.
        """
        self.num_rounds = num_rounds
        self.current_round = None
        self.round_counter = 0

        # Session statistics
        self.wins = 0
        self.losses = 0
        self.ties = 0

    def start_next_round(self):
        """
        Start a new round if the session is not over.

        Returns:
            Round or None: A new Round object, or None if session is finished.
        """
        if self.is_over():
            return None

        self.round_counter += 1

        new_round = Round()
        new_round.start()
        self.current_round = new_round
        return new_round

    def is_over(self):
        """
        Check if all rounds in the session were played.

        Returns:
            bool: True if session is finished, else False.
        """
        return self.round_counter >= self.num_rounds

    def record_outcome(self, outcome):
        """
        Update session statistics based on a round outcome.

        Args:
            outcome (str): One of "BLACKJACK", "WIN", "LOSS", "TIE".

        Raises:
            ValueError: If the outcome is not recognized.
        """
        if outcome in ("BLACKJACK", "WIN"):
            self.wins += 1
        elif outcome == "LOSS":
            self.losses += 1
        elif outcome == "TIE":
            self.ties += 1
        else:
            # Defensive programming: catch invalid outcome values early
            raise ValueError(f"Unknown outcome: {outcome}")
