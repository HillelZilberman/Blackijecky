RANK_TO_STR = {
    1: "A",
    11: "J",
    12: "Q",
    13: "K"
}

SUIT_TO_STR = {
    0: "♠",
    1: "♥",
    2: "♦",
    3: "♣"
}


class Card:
    def __init__(self,rank,suit):
        self.rank = rank
        self.suit = suit

    def get_value(self):
        if self.rank > 10:
            return 10
        elif self.rank == 1:
            return 11
        return self.rank

    def __str__(self):
        rank_str = RANK_TO_STR.get(self.rank, str(self.rank))
        suit_str = SUIT_TO_STR.get(self.suit, str(self.suit))
        return rank_str + suit_str




