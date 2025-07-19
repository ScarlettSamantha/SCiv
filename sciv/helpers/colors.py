import typing
from random import Random
from typing import List, Tuple

Tuple4f = Tuple[float, float, float, float]
Tuple3f = Tuple[float, float, float]


class Colors:
    _sequence_index_basic: int = 0
    _sequence_index_pastel: int = 0
    _sequence_index_all: int = 0

    RESTORE: Tuple4f = (1, 1, 1, 1)

    # Basic colors
    RED: Tuple4f = (1, 0, 0, 1)
    GREEN: Tuple4f = (0, 1, 0, 1)
    BLUE: Tuple4f = (0, 0, 1, 1)
    TIEL: Tuple4f = (0, 0.5, 0.5, 1)
    YELLOW: Tuple4f = (1, 1, 0, 1)
    BLACK: Tuple4f = (0, 0, 0, 1)
    ORANGE: Tuple4f = (1, 0.5, 0, 1)
    PURPLE: Tuple4f = (0.5, 0, 1, 1)
    GREY: Tuple4f = (0.5, 0.5, 0.5, 1)
    WHITE: Tuple4f = (1, 1, 1, 1)
    MAGENTA: Tuple4f = (0.5, 0, 0.5, 1)
    BROWN: Tuple4f = (0.6, 0.3, 0.1, 1)
    MAROON: Tuple4f = (0.5, 0, 0, 1)
    NAVY: Tuple4f = (0, 0, 0.5, 1)
    OLIVE: Tuple4f = (0.5, 0.5, 0, 1)
    INDIGO: Tuple4f = (0.29, 0, 0.51, 1)
    GOLD: Tuple4f = (1.0, 0.84, 0, 1)
    SILVER: Tuple4f = (0.75, 0.75, 0.75, 1)
    CYAN: Tuple4f = (0, 1, 1, 1)
    LIME: Tuple4f = (0.75, 1, 0, 1)
    PINK: Tuple4f = (1, 0.4, 0.7, 1)
    DARK_GREEN: Tuple4f = (0, 0.5, 0, 1)
    LIGHT_GREEN: Tuple4f = (0.5, 1, 0.5, 1)

    COLORS: List[Tuple4f] = [
        RED,
        BLUE,
        YELLOW,
        PURPLE,
        GREEN,
        ORANGE,
        TIEL,
        MAGENTA,
        BLACK,
        GREY,
        BROWN,
        MAROON,
        NAVY,
        OLIVE,
        INDIGO,
        GOLD,
        SILVER,
        CYAN,
        LIME,
        PINK,
        DARK_GREEN,
        LIGHT_GREEN,
    ]

    # Pastel color constants
    PASTEL_PINK: Tuple4f = (1.0, 0.8, 0.8, 1)
    PASTEL_GREEN: Tuple4f = (0.8, 1.0, 0.8, 1)
    PASTEL_BLUE: Tuple4f = (0.8, 0.8, 1.0, 1)
    PASTEL_YELLOW: Tuple4f = (1.0, 1.0, 0.8, 1)
    PASTEL_CYAN: Tuple4f = (0.8, 1.0, 1.0, 1)
    PASTEL_MAGENTA: Tuple4f = (1.0, 0.8, 1.0, 1)
    PASTEL_PEACH: Tuple4f = (0.95, 0.85, 0.7, 1)
    PASTEL_LIME: Tuple4f = (0.85, 0.95, 0.7, 1)
    PASTEL_LAVENDER: Tuple4f = (0.85, 0.7, 0.95, 1)
    PASTEL_SKY: Tuple4f = (0.7, 0.85, 0.95, 1)
    PASTEL_SILVER: Tuple4f = (0.9, 0.9, 0.9, 1)
    PASTEL_KHAKI: Tuple4f = (0.85, 0.85, 0.7, 1)

    PASTELS: List[Tuple4f] = [
        PASTEL_PINK,  # soft warm
        PASTEL_BLUE,  # soft cool
        PASTEL_LIME,  # muted green
        PASTEL_MAGENTA,  # soft bright pink
        PASTEL_SKY,  # soft cyan-blue
        PASTEL_PEACH,  # orangey-light
        PASTEL_LAVENDER,  # pale purple
        PASTEL_GREEN,  # light natural
        PASTEL_KHAKI,  # warm beige
        PASTEL_CYAN,  # soft aqua
        PASTEL_YELLOW,  # soft yellow
        PASTEL_SILVER,  # soft neutral
    ]

    ALL: List[Tuple4f] = COLORS + PASTELS

    @classmethod
    def random(cls, set: str = "all") -> Tuple4f:
        rng = Random()
        if set == "basic":
            return rng.choice(cls.COLORS)
        elif set == "pastel":
            return rng.choice(cls.PASTELS)
        else:
            return rng.choice(cls.ALL)

    @classmethod
    def sequence(cls, set: str = "all") -> Tuple4f:
        if set == "basic":
            if cls._sequence_index_basic >= len(cls.COLORS):
                cls._sequence_index_basic = 0
            color = cls.COLORS[cls._sequence_index_basic]
            cls._sequence_index_basic += 1
            return color
        elif set == "pastel":
            if cls._sequence_index_pastel >= len(cls.PASTELS):
                cls._sequence_index_pastel = 0
            color = cls.PASTELS[cls._sequence_index_pastel]
            cls._sequence_index_pastel += 1
            return color
        else:
            if cls._sequence_index_all >= len(cls.ALL):
                cls._sequence_index_all = 0
            color = cls.ALL[cls._sequence_index_all]
            cls._sequence_index_all += 1
            return color

    @staticmethod
    def t4f_to_t3f(color: Tuple4f) -> Tuple3f:
        return color[:3]

    @staticmethod
    def t4_to_t3(color: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
        return color[:3]

    @staticmethod
    def t4f_to_t4(color: Tuple3f) -> Tuple4f:
        return (color[0], color[1], color[2], 1.0)

    @staticmethod
    def t4f_to_t3(color: Tuple4f) -> Tuple[float, float, float]:
        return (color[0], color[1], color[2])

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
    def to_normalized_float(color: Tuple3f, alpha: float) -> tuple[float, ...]:
        return tuple((*[c / 255.0 for c in color[:3]], alpha))

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

    @staticmethod
    def from_tuple(color: Tuple[float, float, float, float]) -> Tuple4f:
        if len(color) == 3:
            return (color[0], color[1], color[2], 1.0)
        elif len(color) == 4:
            return (color[0], color[1], color[2], color[3])
        else:
            raise ValueError("Color tuple must be of length 3 or 4.")

    @staticmethod
    def closest_color(requested_color: tuple[int, int, int, int]) -> str:
        import webcolors

        min_colors = {}
        for _, name in webcolors.CSS3_NAMES_TO_HEX.items():  # type: ignore
            r_c, g_c, b_c = webcolors.hex_to_rgb(name)  # type: ignore
            rd: int = (r_c - requested_color[0]) ** 2
            gd: int = (g_c - requested_color[1]) ** 2
            bd: int = (b_c - requested_color[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        return min_colors[min(min_colors.keys())]  # type: ignore

    @staticmethod
    def convert_rgba_to_color_name(rgba: tuple[int, int, int, int]) -> str:
        import webcolors

        if rgba.__len__() == 4:
            rgb: Tuple[int, int, int] = rgba[:3]  # type: ignore # Ignore the alpha channel for color matching
        else:
            rgb: Tuple[int, int, int, int] = rgba
        try:
            # Get the closest color name directly
            closest_name = webcolors.rgb_to_name(rgb)  # type: ignore ,This is a known issue with the library. It works.
        except ValueError:
            from helpers.colors import Colors

            closest_name = Colors.closest_color(rgb)
        return closest_name
