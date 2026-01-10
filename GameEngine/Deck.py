import random

from GameEngine.Card import Card

class Deck:
    def __init__(self):
        self.deck = []
        for suit in range(4):
            for value in range(1,14):
                self.deck.append(Card(value, suit))

    def shuffle(self):
        random.shuffle(self.deck)

    def draw(self):
        return self.deck.pop()

    def get_length(self):
        return len(self.deck)




