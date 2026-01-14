"""
card.py

Defines a Card object for a standard playing-card deck.

- Ranks are represented as integers:
  1 = Ace, 11 = Jack, 12 = Queen, 13 = King, and 2-10 as their numbers.
- Suits are represented as integers:
  0 = Spades, 1 = Hearts, 2 = Diamonds, 3 = Clubs.

This module also provides string representations for ranks and suits.
"""

RANK_TO_STR = {
    1: "A",
    11: "J",
    12: "Q",
    13: "K",
}

SUIT_TO_STR = {
    0: "♠",
    1: "♥",
    2: "♦",
    3: "♣",
}


class Card:
    """
    Represents a single playing card.

    Attributes:
        rank (int): The card rank (1-13).
        suit (int): The card suit (0-3).

    Notes:
        get_value() is tailored for Blackjack-like rules:
        - Face cards (J/Q/K) are worth 10
        - Ace is returned as 11 by default (Ace-as-1 is typically handled elsewhere, e.g., in Hand logic)
    """

    def __init__(self, rank, suit):
        """
        Create a new card with a given rank and suit.

        Args:
            rank (int): Rank of the card (1-13).
            suit (int): Suit of the card (0-3).
        """
        self.rank = rank
        self.suit = suit

    def get_value(self):
        """
        Return the card's numeric value according to Blackjack rules.

        Returns:
            int: 10 for face cards, 11 for Ace, otherwise the numeric rank.
        """
        # J, Q, K -> 10
        if self.rank > 10:
            return 10
        # Ace -> 11 (handling Ace=1 is usually done in Hand)
        elif self.rank == 1:
            return 11
        return self.rank

    def __str__(self):
        """
        Return a human-readable string representation of the card.

        Examples:
            'A♠', '10♥', 'K♦'

        Returns:
            str: Rank + suit as a single string.
        """
        # Fall back to the raw numeric string if a mapping is missing
        rank_str = RANK_TO_STR.get(self.rank, str(self.rank))
        suit_str = SUIT_TO_STR.get(self.suit, str(self.suit))
        return rank_str + suit_str
