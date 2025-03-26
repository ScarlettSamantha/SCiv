import typing
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
    WHITE: Tuple4f = (1, 1, 1, 1)

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

    @staticmethod
    def to_hex(color: Tuple3f | Tuple4f, strip_alpha: bool = True) -> str:
        if len(color) == 4:
            if strip_alpha:
                color = color[:3]
            else:
                return "#{:02x}{:02x}{:02x}{:02x}".format(
                    int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), int(color[3] * 255)
                )
        return "#{:02x}{:02x}{:02x}".format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

    @staticmethod
    def to_rgba(color: Tuple4f) -> str:
        return "rgba({}, {}, {}, {})".format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), color[3])

    @staticmethod
    def to_rgb(color: Tuple4f) -> str:
        return "rgb({}, {}, {})".format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

    @staticmethod
    def from_hex(hex_color: str) -> Tuple3f:
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
        return typing.cast(Tuple3f, rgb)

    @staticmethod
    def from_rgba(rgba_color: str) -> Tuple4f:
        _rgba_color: list[str] = rgba_color.lstrip("rgba(").rstrip(")").split(",")
        rgba = tuple(int(_rgba_color[i]) / 255 for i in (0, 1, 2, 3))
        return typing.cast(Tuple4f, rgba)
