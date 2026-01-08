VALUE_TO_STR = {
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
    def __init__(self,value,suit):
        self.value = value
        self.suit = suit

    def __str__(self):
        value_str = VALUE_TO_STR.get(self.value, str(self.value))
        suit_str = SUIT_TO_STR.get(self.suit, str(self.suit))
        return value_str + suit_str



def main():
    card = Card(10, 11)
    print(card)

if __name__ == '__main__':
    main()