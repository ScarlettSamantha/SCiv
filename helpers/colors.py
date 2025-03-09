from random import Random
from typing import List, Tuple

Tuple4f = Tuple[float, float, float, float]
Tuple3f = Tuple[float, float, float]


class Colors:
    _sequence_index: int = 0

    RESTORE: Tuple4f = (1, 1, 1, 1)

    RED: Tuple4f = (1, 0, 0, 1)
    GREEN: Tuple4f = (0, 1, 0, 1)
    BLUE: Tuple4f = (0, 0, 1, 1)
    TIEL: Tuple4f = (0.5, 0.2, 0.7, 1)
    YELLOW: Tuple4f = (1, 1, 0, 1)
    BLACK: Tuple4f = (0, 0, 0, 1)
    ORANGE: Tuple4f = (1, 0.5, 0, 1)
    PURPLE: Tuple4f = (0.5, 0, 1, 1)
    GREY: Tuple4f = (0.5, 0.5, 0.5, 1)

    COLORS: List[Tuple4f] = [
        RED,
        GREEN,
        BLUE,
        YELLOW,
        TIEL,
        BLACK,
        ORANGE,
        PURPLE,
        GREY,
    ]

    @classmethod
    def random(cls) -> Tuple4f:
        rng = Random()
        choice: Tuple4f = rng.choice(cls.COLORS)
        return choice

    @classmethod
    def sequence(cls) -> Tuple4f:
        if cls._sequence_index >= len(cls.COLORS):
            cls._sequence_index = 0
        color = cls.COLORS[cls._sequence_index]
        cls._sequence_index += 1
        return color
