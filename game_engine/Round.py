from game_engine.Deck import Deck
from game_engine.Hand import Hand
from enum import Enum

decision = {"HIT", "STAND"}
outcome = {"WIN", "LOSS", "TIE", "BLACKJACK"}

class RoundState(Enum):
    PLAYER_TURN = 0
    DEALER_TURN = 1
    ROUND_OVER = 2

class Round():
    def __init__(self):
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.state = None
        self.dealer_hidden = True
        self.outcome = None

    def start(self):
        self.deck.shuffle()
        for card in range(2):
            self.player_hand.add_card(self.deck.draw())
            self.dealer_hand.add_card(self.deck.draw())
        if self.player_hand.hand_sum() == 21:
            self.outcome = "BLACKJACK"
            self.state = RoundState.ROUND_OVER
        self.state = RoundState.PLAYER_TURN

    def need_player_decision(self):
        if self.state == RoundState.PLAYER_TURN and not self.player_hand.is_bust():
            return True
        else:
            return False

    def game_decision(self):
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
        if self.state == RoundState.DEALER_TURN:
            self.dealer_hidden = False
            while self.dealer_hand.hand_sum() < 17:
                self.dealer_hand.add_card(self.deck.draw())

            if self.dealer_hand.is_bust():
                self.outcome = "WIN"
                self.state = RoundState.ROUND_OVER
            else:
                self.game_decision()

    def apply_player_decision(self, decision):
        if decision == "HIT":
            self.player_hand.add_card(self.deck.draw())
            if self.player_hand.is_bust():
                self.outcome = "LOSS"
                self.state = RoundState.ROUND_OVER

        else:
            self.state = RoundState.DEALER_TURN
            self.play_dealer_turn()







