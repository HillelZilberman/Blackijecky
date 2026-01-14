class Hand:
    """
    Represents a player's hand of cards.

    This class is designed mainly for Blackjack-like rules:
    - Aces can be worth 11 or 1, depending on the total hand value.
    """

    def __init__(self):
        """
        Create an empty hand.
        """
        self.hand = []

    def add_card(self, card):
        """
        Add a card to the hand.

        Args:
            card (Card): Card object to add.
        """
        self.hand.append(card)

    def hand_sum(self):
        """
        Calculate the total value of the hand using Blackjack rules.

        Logic:
        - All cards are summed using Card.get_value().
        - Aces start as 11.
        - If total > 21, each Ace can be converted from 11 to 1 by subtracting 10.

        Returns:
            int: Final hand value.
        """
        total = 0
        aces = 0

        for card in self.hand:
            if card.rank == 1:
                aces += 1  # Count how many Aces we have
            total += card.get_value()

        # If the hand is bust and there are Aces,
        # convert Aces from 11 to 1 until total <= 21 or no Aces left
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def is_bust(self):
        """
        Check if the hand is bust (over 21).

        Returns:
            bool: True if hand value > 21, else False.
        """
        return self.hand_sum() > 21

    def __str__(self):
        """
        Return a multi-line string of all cards in the hand.

        Returns:
            str: Each card on its own line.
        """
        hand_str = ''
        for card in self.hand:
            hand_str += card.__str__() + '\n'
        return hand_str
