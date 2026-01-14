import random
from game_engine.Card import Card


class Deck:
    """
    Represents a standard 52-card deck.

    The deck is built using:
    - 4 suits (0-3)
    - 13 ranks (1-13)

    Cards are stored internally in a list, where the end of the list
    is treated as the "top" of the deck when drawing.
    """

    def __init__(self):
        """
        Create a full deck of 52 cards in ordered form.

        Order:
            First by suit (0 to 3),
            Then by rank (1 to 13) for each suit.
        """
        self.deck = []
        for suit in range(4):
            for value in range(1, 14):
                self.deck.append(Card(value, suit))

    def shuffle(self):
        """
        Shuffle the deck randomly in-place.
        """
        random.shuffle(self.deck)

    def draw(self):
        """
        Draw and remove the top card from the deck.

        Returns:
            Card: The last card in the list.

        Notes:
            Assumes the deck is not empty.
            Caller is responsible for checking deck size if needed.
        """
        return self.deck.pop()

    def get_length(self):
        """
        Get the number of remaining cards in the deck.

        Returns:
            int: Current deck size.
        """
        return len(self.deck)
