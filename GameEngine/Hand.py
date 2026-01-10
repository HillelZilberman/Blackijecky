class Hand:
    def __init__(self):
        self.hand = []

    def add_card(self, card):
        self.hand.append(card)

    def hand_sum(self):
        total = 0
        for card in self.hand:
            total += card.get_value()
        return total

    def is_bust(self):
        return self.hand_sum() > 21

    def __str__(self):
        hand_str = ''
        for card in self.hand:
            hand_str += card.__str__() + '\n'
        return hand_str

