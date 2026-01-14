from game_engine.Deck import Deck
from game_engine.Hand import Hand
from enum import Enum

# Possible player decisions
decision = {"HIT", "STAND"}

# Possible round outcomes
outcome = {"WIN", "LOSS", "TIE", "BLACKJACK"}


class RoundState(Enum):
    """
    Represents the current phase of the round.
    """
    PLAYER_TURN = 0
    DEALER_TURN = 1
    ROUND_OVER = 2


class Round:
    """
    Represents a single round of Blackjack.

    Manages:
    - Deck creation and shuffling
    - Player and dealer hands
    - Turn state (player, dealer, or round over)
    - Final outcome of the round
    """

    def __init__(self):
        """
        Initialize a new round with empty hands and a fresh deck.
        """
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.state = None
        self.dealer_hidden = True   # Dealer's first card is hidden at start
        self.outcome = None

    def start(self):
        """
        Start the round:
        - Shuffle the deck
        - Deal 2 cards to player and dealer
        - Check for immediate Blackjack
        """
        self.deck.shuffle()

        for _ in range(2):
            self.player_hand.add_card(self.deck.draw())
            self.dealer_hand.add_card(self.deck.draw())

        # Check for player Blackjack right after dealing
        if self.player_hand.hand_sum() == 21:
            self.outcome = "BLACKJACK"
            self.state = RoundState.ROUND_OVER

        # If not over, player starts
        self.state = RoundState.PLAYER_TURN

    def need_player_decision(self):
        """
        Check if the game is waiting for the player's move.

        Returns:
            bool: True if it's player's turn and player is not bust.
        """
        if self.state == RoundState.PLAYER_TURN and not self.player_hand.is_bust():
            return True
        else:
            return False

    def game_decision(self):
        """
        Compare player and dealer hands and decide the outcome.
        """
        if self.player_hand.hand_sum() > self.dealer_hand.hand_sum():
            self.outcome = "WIN"
            self.state = RoundState.ROUND_OVER
        elif self.player_hand.hand_sum() < self.dealer_hand.hand_sum():
            self.outcome = "LOSS"
            self.state = RoundState.ROUND_OVER
        else:
            self.outcome = "TIE"
            self.state = RoundState.ROUND_OVER

    def play_dealer_turn(self):
        """
        Execute the dealer's turn:
        - Reveal hidden card
        - Draw until dealer has at least 17
        - Decide winner
        """
        if self.state == RoundState.DEALER_TURN:
            self.dealer_hidden = False

            # Dealer must draw until reaching 17 or more
            while self.dealer_hand.hand_sum() < 17:
                self.dealer_hand.add_card(self.deck.draw())

            if self.dealer_hand.is_bust():
                self.outcome = "WIN"
                self.state = RoundState.ROUND_OVER
            else:
                self.game_decision()

    def apply_player_decision(self, decision):
        """
        Apply the player's action (HIT or STAND).

        Args:
            decision (str): "HIT" or "STAND"
        """
        if decision == "HIT":
            self.player_hand.add_card(self.deck.draw())

            # If player busts, round ends immediately
            if self.player_hand.is_bust():
                self.outcome = "LOSS"
                self.state = RoundState.ROUND_OVER
        else:
            # Player stands -> dealer's turn starts
            self.state = RoundState.DEALER_TURN
            self.play_dealer_turn()
