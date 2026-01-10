class Hand:
    def __init__(self):
        self.hand = []

    def add_card(self, card):
        self.hand.append(card)

    def hand_sum(self):
        total = 0
        aces = 0
        for card in self.hand:
            if card.rank == 1:
                aces += 1
            total += card.get_value()
        # If the hand busted and there is aces, choose ace to the value of 1
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_bust(self):
        return self.hand_sum() > 21

    def __str__(self):
        hand_str = ''
        for card in self.hand:
            hand_str += card.__str__() + '\n'
        return hand_str

