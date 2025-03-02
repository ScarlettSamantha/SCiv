from typing import Dict, List, Any, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from gameplay.resource import BaseResource


class TileYield:
    BASE: int = 0
    ADDITIVE: int = 1

    PERCENTAGE_CUMMULATIVE: int = 2
    PERCENTAGE_ADDATIVE: int = 3

    MODE_STR: Dict[int, str] = {
        BASE: "BASE",
        ADDITIVE: "ADDATIVE",
        PERCENTAGE_CUMMULATIVE: "PERCENTAGE_CUMMULATIVE",
        PERCENTAGE_ADDATIVE: "PERCENTAGE_ADDATIVE",
    }

    # Percentages need to be a 0.0 = 0 percentage in or decrease while 1.0 is a 100% increase and a -1.0 is a 100% decrease.
    # Absolute numbers are taken as a float but *should* be treated more like integers and are going to be rounded at the end.
    def __init__(
        self,
        name: str | None = None,
        gold: float = 0.0,
        production: float = 0.0,
        science: float = 0.0,
        food: float = 0.0,
        culture: float = 0.0,
        housing: float = 0.0,
        faith: float = 0.0,
        mode: int = 1,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Initialize the attributes specific to TileYield
        self._name: str | None = name
        self.mode: int = mode

        from gameplay.resources.core.basic.culture import Culture
        from gameplay.resources.core.basic.faith import Faith
        from gameplay.resources.core.basic.food import Food
        from gameplay.resources.core.basic.gold import Gold
        from gameplay.resources.core.basic.housing import Housing
        from gameplay.resources.core.basic.production import Production
        from gameplay.resources.core.basic.science import Science

        from gameplay.resources.core.mechanics.stability import Stability
        from gameplay.resources.core.mechanics.contentment import Contentment
        from gameplay.resources.core.mechanics.angre import Angre
        from gameplay.resources.core.mechanics.revolt import Revolt

        from gameplay.resources.core.mechanics.greats import (
            GreatArtist,
            GreatCommerece,
            GreatMilitary,
            GreatEngineer,
            GreatScientist,
            GreatHero,
            GreatHoly,
        )

        self.gold: Gold = Gold(value=gold)
        self.production = Production(value=production)
        self.science = Science(value=science)
        self.food = Food(value=food)
        self.culture = Culture(value=culture)
        self.housing = Housing(value=housing)
        self.faith = Faith(value=faith)

        self.contentment = Contentment(value=0.0)
        self.angre = Angre(value=0.0)
        self.revolt = Revolt(value=0.0)
        self.stability = Stability(value=0.0)

        self.great_person_science = GreatScientist(value=0.0)
        self.great_person_production = GreatEngineer(value=0.0)
        self.great_person_artist = GreatArtist(value=0.0)
        self.great_person_military = GreatMilitary(value=0.0)
        self.great_person_commerce = GreatCommerece(value=0.0)
        self.great_person_hero = GreatHero(value=0.0)
        self.great_person_holy = GreatHoly(value=0.0)

        self._calculatable_properties: List[str] = [
            "gold",
            "production",
            "science",
            "food",
            "culture",
            "housing",
            "faith",
        ]
        self._mechanic_resources: List[str] = ["contentment", "angre", "revolt", "stability"]
        self._calculatable_great_people: List[str] = [
            "science",
            "production",
            "artist",
            "military",
            "commerce",
            "hero",
            "holy",
        ]

        self.other_mechnics: Dict[str, "BaseResource"] = {}

    @property
    def name(self) -> None | str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def __repr__(self) -> str:
        return f"TileYield<Mode:{self.MODE_STR[self.mode]}>g:<{self.gold}>|p:<{self.production}>|s:<{self.science}>|f:<{self.food}>|c:<{self.culture}>|h:<{self.housing}>|fa:<{self.faith}>"

    def __add__(self, b: "TileYield") -> Self:
        return self.add(tile_yield=b)

    def __mul__(self, b: "TileYield") -> Self:
        return self.multiply(tile_yield=b)

    def set_prop(self, name: str, value: Any):
        if name in self.calculatable_great_people() + self.calculatable_properties():
            raise ValueError(f"cannot set property[{name}] as it does not exist or is accessable")
        setattr(self, name, value)

    def get_prop(self, name: str) -> Any:
        if name not in self.calculatable_great_people() + self.calculatable_properties():
            raise ValueError(f"cannot get property[{name}] as it does not exist or is accessable")
        return getattr(self, name)

    def export_basic(self) -> List["BaseResource"]:
        resources: List["BaseResource"] = [
            self.gold,
            self.production,
            self.food,
            self.science,
            self.culture,
        ]
        return resources

    def add(self, tile_yield: "TileYield") -> Self:
        # Process simple calculatable properties
        for prop in self.calculatable_properties():
            current = getattr(self, prop)  # e.g. Gold, Production, etc.
            addition = getattr(tile_yield, prop)
            new_val = current.value + addition.value
            setattr(self, prop, type(current)(value=new_val))

        # Process mechanic resources similarly
        for prop in self.mechanic_resources():
            current = getattr(self, prop)
            addition = getattr(tile_yield, prop)
            new_val = current.value + addition.value
            setattr(self, prop, type(current)(value=new_val))

        # Process great people, noting the attribute naming convention
        for prop in self.calculatable_great_people():
            current = getattr(self, f"great_person_{prop}")
            addition = getattr(tile_yield, f"great_person_{prop}")
            new_val = current.value + addition.value
            setattr(self, f"great_person_{prop}", type(current)(value=new_val))

        # Process other mechanics if available
        for key, mechanic in self.other_mechnics.items():
            if key not in tile_yield.other_mechnics:
                continue
            current = mechanic
            addition = getattr(tile_yield, str(mechanic))
            new_val = current.value + addition.value
            self.other_mechnics[key] = type(current)(value=new_val)

        return self

    def multiply(self, tile_yield: "TileYield") -> Self:
        # Multiply calculatable properties
        for prop in self.calculatable_properties():
            multiplicative = getattr(tile_yield, prop)
            # Skip multiplicative identities
            if multiplicative.value in {0.0, 1.0, -1.0}:
                continue
            current = getattr(self, prop)
            new_val = current.value * multiplicative.value
            setattr(self, prop, type(current)(value=new_val))

        # Multiply mechanic resources
        for prop in self.mechanic_resources():
            multiplicative = getattr(tile_yield, prop)
            current = getattr(self, prop)
            new_val = current.value * multiplicative.value
            setattr(self, prop, type(current)(value=new_val))

        # Multiply great people yields
        for prop in self.calculatable_great_people():
            multiplicative = getattr(tile_yield, f"great_person_{prop}")
            current = getattr(self, f"great_person_{prop}")
            new_val = current.value * multiplicative.value
            setattr(self, f"great_person_{prop}", type(current)(value=new_val))

        # Multiply other mechanics if available
        for key, mechanic in self.other_mechnics.items():
            if key not in tile_yield.other_mechnics:
                continue
            multiplicative = getattr(tile_yield, str(mechanic))
            current = mechanic
            new_val = current.value * multiplicative.value
            self.other_mechnics[key] = type(current)(value=new_val)

        return self

    def calculate(self) -> None:
        pass

    def props(self) -> Dict[Any, Any]:
        a: Dict[Any, Any] = {}
        for item in self.calculatable_properties():
            a[item] = getattr(self, item)
        return a

    def convert_short_great_to_long(self, value: str) -> str:
        if value not in self.calculatable_great_people():
            raise TypeError(
                f"Cannot convert short to long name because great type does not seem to exist {type(value)}"
            )
        return f"great_person_{value}"

    def calculatable_properties(self) -> List[str]:
        return self._calculatable_properties

    def mechanic_resources(self) -> List[str]:
        return self._mechanic_resources

    def calculatable_great_people(self) -> List[str]:
        return self._calculatable_great_people

    @staticmethod
    def baseYield() -> "TileYield":
        return TileYield()

    @staticmethod
    def nullYield() -> "TileYield":
        return TileYield(gold=0.0, production=0.0, science=0.0, food=0.0, culture=0.0, housing=0.0, faith=0.0)

    def __str__(self) -> str:
        return self.__repr__()

    def __len__(self) -> int:
        total = 0
        for property in self.calculatable_properties():
            total += getattr(self, property)
        return int(total)
