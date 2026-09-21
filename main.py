import random
import time

from typing import Literal, Sequence
import matplotlib.pyplot as plt

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

SOFT_TOTALS: list[list[Action]] = list(
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
        self.cut = int(decks * 52 * ((random.random() - 0.5) * 0.1 + 0.7))

        self._deck = (list(range(2, 12)) + [10] * 3) * 4 * decks
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


def visualize(
    dealer: tuple[int, ...],
    hands: tuple[tuple[tuple[int, ...], Action], ...],
    bet: float,
    chips: float,
    shoe: Shoe,
) -> None:
    print("Shoe")
    print(f"  RC: {shoe._count}")
    print(f"  TC: {shoe.true_count}")
    print(f"Bet: {bet}, Chips: {chips}")
    print(f"Dealer: {dealer} ({evaluate(dealer)})")
    print("Hands:")
    for hand, last_action in hands:
        print(
            f"  {hand} [{last_action}] ({evaluate(hand)}) {{{bet_outcom(dealer, (hand, last_action)) * bet}}}"
        )
    print("************************************")


def bet_outcom(dealer: tuple[int, ...], hand: tuple[tuple[int, ...], Action]) -> float:
    cards, last_action = hand
    hand_value = evaluate(cards)
    dealer_value = evaluate(dealer)
    dub_mult = 2.0 if last_action == "D" else 1.0

    if hand_value > 21:
        return -1.0 * dub_mult
    if last_action == "SUR":
        assert len(cards) == 2, "Cannot surrender after hitting"
        return -0.5
    if (
        len(cards) == 2
        and hand_value == 21
        and not (len(dealer) == 2 and dealer_value == 21)
    ):
        return 1.5
    if dealer_value > 21 or hand_value > dealer_value:
        return 1 * dub_mult
    if dealer_value == hand_value:
        return 0

    return -1 * dub_mult


def run() -> list[float]:
    shoe = Shoe(6)
    chips = 0.0
    wins = [0.0, 0.0]
    hand_count = 0
    history = [chips]

    while not shoe.should_stop():
        bet = max(1.0, shoe.true_count * 10.0)
        dealer_hand: tuple[int, ...] = (shoe.pop(), shoe.pop())
        hands = play_hand((shoe.pop(),), dealer_hand[0], shoe)
        dealer_hand = play_dealer(dealer_hand, shoe)

        for hand, last_action in hands:
            hand_count += 1
            change = bet * bet_outcom(dealer_hand, (hand, last_action))
            chips += change

            if change > 0:
                wins[0] = wins[0] + change
            else:
                wins[1] = wins[1] - change

        history.append(chips)
        # visualize(dealer_hand, hands, bet, chips, shoe)

    return history


def avg(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


if __name__ == "__main__":
    history = [run() for _ in range(10000)]
    avg_history = [
        avg([h[i] for h in history if i < len(h)])
        for i in range(max([len(h) for h in history]))
    ]
    plt.plot(range(len(avg_history[:-3])), avg_history[:-3])
    plt.show()
