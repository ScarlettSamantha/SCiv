from typing import TYPE_CHECKING, Any, Generator, List, Tuple, Type

from gameplay.age import Age
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStr, t_

if TYPE_CHECKING:
    from system.entity import BaseEntity
    from gameplay.player import Player


class Tech:
    requires: List[Type["Tech"]] = []
    key: str
    name: T_TranslationOrStr | None = None
    description: T_TranslationOrStr | None = None

    _icon: T_TranslationOrStr | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.TIEL

    tech_points_required: int = 1
    age: Age | None = None
    color: Tuple[int, int, int, int] | None = None
    contributes_to: List[Type["Tech"]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.key: str = self.key

        self.name: T_TranslationOrStr | None = self.name if self.name is not None else t_(f"tech.{self.key}.name")
        self.description: T_TranslationOrStr | None = (
            self.description if self.description is not None else t_(f"tech.{self.key}.description")
        )
        self.icon: T_TranslationOrStr | None = (
            self.description if self.description is not None else t_(f"tech.{self.key}.description")  # type: ignore
        )
        self.color: Tuple[int, int, int, int] | None = self.color

        self.completed = False
        self.tech_points_required: int = self.tech_points_required
        self.age: Age | None = self.age

    def __repr__(self, recursive: bool = False):
        return f"{self.name}"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Tech):
            return self.name == other.name
        return False

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        return [] + cls.contributes_to  # type: ignore

    @classmethod
    def on_tooltip(cls) -> str:
        return f"[b]{str(cls.name)}[/b]\n\n[i]Costs:[/i] {cls.tech_points_required} points\n\n{str(cls.description)}"  # type: ignore

    @classmethod
    def get_icon(cls) -> T_TranslationOrStr:
        return cls._icon if cls._icon is not None else Placeholder.getPlaceholderImagePathSmallIcon()

    @classmethod
    def set_icon(cls, value: T_TranslationOrStr) -> None:
        cls._icon = value

    def on_unlock(self, player: "Player") -> None: ...


class TechTree:
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    icon: T_TranslationOrStr | None = None

    def __init__(self):
        self._items: List[Type[Tech]] = []
        self._ages: List[Age] = []  # noqa F821

    def items(self) -> Generator[Type[Tech], None, None]:
        for item in self._items:
            yield item

    def add(self, item: Type[Tech]) -> None:
        self._items.append(item)

    def add_age(self, age: Age) -> None:
        self._ages.append(age)

    @classmethod
    def closest_color(cls, requested_color: tuple[int, int, int, int]) -> str:
        import webcolors

        min_colors = {}
        for _, name in webcolors.CSS3_NAMES_TO_HEX.items():  # type: ignore
            r_c, g_c, b_c = webcolors.hex_to_rgb(name)  # type: ignore
            rd: int = (r_c - requested_color[0]) ** 2
            gd: int = (g_c - requested_color[1]) ** 2
            bd: int = (b_c - requested_color[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        return min_colors[min(min_colors.keys())]  # type: ignore

    @classmethod
    def convert_rgba_to_color_name(cls, rgba: tuple[int, int, int, int]) -> str:
        import webcolors

        if rgba.__len__() == 4:
            rgb: Tuple[int, int, int] = rgba[:3]  # type: ignore # Ignore the alpha channel for color matching
        else:
            rgb: Tuple[int, int, int, int] = rgba
        try:
            # Get the closest color name directly
            closest_name = webcolors.rgb_to_name(rgb)  # type: ignore , This is a known issue with the library. It works.
        except ValueError:
            # Find the closest color name using the colormath library
            closest_name = cls.closest_color(rgb)
        return closest_name
