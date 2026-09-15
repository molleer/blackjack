import random
import time

from typing import Literal


random.seed(int(time.time()))
"""
Rules:
3:2 black jack
Double allowed
Double after split allowed
Late surrender allowed
Late surrender after splitting allowed
"""

Action = Literal["S", "H", "D", "Ds", "SP", "SUR"]

HARD_TOTALS: list[list[Action]] = list(
    reversed(
        [
            # Dealer Upcard
            # 2    3    4    5    6    7    8    9   10    A
            ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],  # 17
            ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],  # 16
            ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],  # 15
            ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],  # 14
            ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],  # 13
            ["H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],  # 12
            ["D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],  # 11
            ["D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],  # 10
            ["H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],  # 9
            ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],  # 8
        ]
    )
)

SPLITS = list(
    reversed(
        [
            # Dealer upcard
            # 2  3  4  5  6  7  8  9 10 A
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # AA
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # TT
            [1, 1, 1, 1, 1, 0, 1, 1, 0, 0],  # 99
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # 88
            [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # 77
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # 66
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 55
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],  # 44
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # 33
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # 22
        ]
    )
)

SOFT_TOTALS = list(
    reversed(
        [
            # Dealer Upcard
            # 2    3    4    5    6    7    8    9   10    A
            ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],  # 9
            ["S", "S", "S", "S", "Ds", "S", "S", "S", "S", "S"],  # 8
            ["Ds", "Ds", "Ds", "Ds", "Ds", "S", "S", "H", "H", "H"],  # 7
            ["H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],  # 6
            ["H", "H", "D", "D", "D", "H", "H", "H", "H", "H"],  # 5
            ["H", "H", "D", "D", "D", "H", "H", "H", "H", "H"],  # 4
            ["H", "H", "H", "D", "D", "H", "H", "H", "H", "H"],  # 3
            ["H", "H", "H", "D", "D", "H", "H", "H", "H", "H"],  # 2
        ]
    )
)

LATE_SURR = list(
    reversed(
        [
            # Dealer upcard
            # 2  3  4  5  6  7  8  9 10 A
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 17
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 16
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 15
        ]
    )
)


class Shoe:
    def __init__(self, decks: int = 6):
        self.cut = int(decks * 52 * 0.75)

        self._deck = list(range(2, 12)) * 4 * decks
        random.shuffle(self._deck)
        self._delt = 0

        self._count = 0

    def should_stop(self) -> bool:
        return self._delt >= self.cut

    @property
    def true_count(self) -> int:
        return round(self._count / (len(self._deck) / 52.0))

    def pop(self) -> int:
        self._delt += 1
        if len(self._deck) == 0:
            return random.choice(range(2, 12))

        card = self._deck.pop()

        if card <= 6:
            self._count += 1
        if card >= 10:
            self._count -= 1

        return card


def _hard_step(hand: tuple[int, ...], upcard: int) -> Action:
    hand_value = evaluate(hand)
    if hand_value > 17:
        return "S"

    if hand_value < 8:
        return "H"

    return HARD_TOTALS[hand_value - 8][upcard - 2]


def _soft_step(hand: tuple[int, ...], upcard: int) -> Action:
    if evaluate(hand) >= 21:
        return "S"

    non_ace_value = sum(card for card in hand if card != 11)
    return SOFT_TOTALS[non_ace_value - 2][upcard - 2]


def _surrender(hand: tuple[int, ...], upcard) -> bool:
    value = evaluate(hand)
    if len(hand) > 2 or value > 17 or value < 15:
        return False
    return LATE_SURR[value - 15][upcard - 2]


def _is_soft(hand: tuple[int, ...]) -> bool:
    n_ases = sum(1 for card in hand if card == 11)
    return n_ases > 0 and sum(hand) - n_ases * 10 <= 10


def _split(hand: tuple[int, ...], upcard: int) -> bool:
    if len(hand) > 2 or hand[0] != hand[1]:
        return False

    return SPLITS[hand[0] - 2][upcard - 2] == 1


def step(hand: tuple[int, ...], upcard: int) -> Action:
    if evaluate(hand) == 21:
        return "S"

    if _surrender(hand, upcard):
        return "SUR"

    if _split(hand, upcard):
        return "SP"

    if _is_soft(hand):
        return _soft_step(hand, upcard)

    return _hard_step(hand, upcard)


def evaluate(hand: tuple[int, ...]) -> int:
    n_ases = sum(1 for card in hand if card == 11)
    value = sum(hand)
    for _ in range(n_ases):
        if value <= 21:
            return value
        value -= 10

    return value


def play_hand(
    hand: tuple[int, ...], upcard: int, shoe: Shoe
) -> tuple[tuple[tuple[int, ...], Action], ...]:
    hand = (*hand, shoe.pop())
    action = step(hand, upcard)

    if action == "H" or len(hand) > 2 and action == "D":
        return (*play_hand(hand, upcard, shoe),)
    elif action == "D" or action == "Ds":
        return (((*hand, shoe.pop()), "D"),)
    elif action == "SP":
        return (
            *play_hand((hand[0],), upcard, shoe),
            *play_hand((hand[1],), upcard, shoe),
        )

    return ((hand, action),)


def play_dealer(hand: tuple[int, ...], shoe: Shoe) -> tuple[int, ...]:
    value = evaluate(hand)
    if value >= 17:
        return hand

    return play_dealer((*hand, shoe.pop()), shoe)


def run() -> float:
    shoe = Shoe(6)
    chips = 0.0
    hand_count = 0

    while not shoe.should_stop():
        bet = max(1.0, max(shoe.true_count, 0) * 10.0)
        dealer_hand: tuple[int, ...] = (shoe.pop(), shoe.pop())
        hands = play_hand((shoe.pop(),), dealer_hand[0], shoe)
        dealer_hand = play_dealer(dealer_hand, shoe)
        dealer_value = evaluate(dealer_hand)

        for hand, last_action in hands:
            hand_count += 1
            hand_value = evaluate(hand)
            hand_bet = 2 * bet if last_action == "D" else bet

            if last_action == "SUR":
                chips -= 0.5 * bet
            if hand_value > 21:
                chips -= hand_bet
            elif dealer_value > 21 or hand_value > dealer_value:
                chips += hand_bet

    return chips


if __name__ == "__main__":
    shoes = 10000
    chips = sum(run() for _ in range(shoes))
    print(f"EV/shoe: {chips / shoes}")
