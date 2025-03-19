import copy
from typing import TYPE_CHECKING, Any, Dict, List, Self

if TYPE_CHECKING:
    from gameplay.resource import BaseResource
    from gameplay.resources.core.basic.culture import Culture
    from gameplay.resources.core.basic.faith import Faith
    from gameplay.resources.core.basic.food import Food
    from gameplay.resources.core.basic.gold import Gold
    from gameplay.resources.core.basic.housing import Housing
    from gameplay.resources.core.basic.production import Production
    from gameplay.resources.core.basic.science import Science


class Yields:
    BASE: int = 0
    ADDITIVE: int = 1
    PERCENTAGE_CUMULATIVE: int = 2
    PERCENTAGE_ADDITIVE: int = 3

    MODE_STR: Dict[int, str] = {
        BASE: "BASE",
        ADDITIVE: "ADDITIVE",
        PERCENTAGE_CUMULATIVE: "PERCENTAGE_CUMULATIVE",
        PERCENTAGE_ADDITIVE: "PERCENTAGE_ADDITIVE",
    }

    # Percentages: 0.0 = 0% change, 1.0 = +100%, -1.0 = -100%
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
        mode: int = ADDITIVE,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._name: str | None = name
        self.mode: int = mode

        self._gold: float | int = gold
        self._production: float | int = production
        self._science: float | int = science
        self._food: float | int = food
        self._culture: float | int = culture
        self._housing: float | int = housing
        self._faith: float | int = faith

        self._contentment: float | int = 0.0
        self._angre: float | int = 0.0
        self._revolt: float | int = 0.0
        self._stability: float | int = 0.0

        self._great_person_science: float | int = 0.0
        self._great_person_production: float | int = 0.0
        self._great_person_artist: float | int = 0.0
        self._great_person_military: float | int = 0.0
        self._great_person_commerce: float | int = 0.0
        self._great_person_hero: float | int = 0.0
        self._great_person_holy: float | int = 0.0

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

    @property
    def name(self) -> None | str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def gold(self) -> "BaseResource":
        from gameplay.resources.core.basic.gold import Gold

        return Gold(value=self._gold)

    @gold.setter
    def gold(self, value: "float | Yields | Gold") -> None:
        from gameplay.resources.core.basic.gold import Gold

        if isinstance(value, Gold):
            self._gold = value.value
        elif isinstance(value, (int, float)):
            self._gold = value
        elif isinstance(value, Yields):
            self._gold = value.gold.value

    @property
    def production(self) -> "BaseResource":
        from gameplay.resources.core.basic.production import Production

        return Production(value=self._production)

    @production.setter
    def production(self, value: "float | Yields | Production") -> None:
        from gameplay.resources.core.basic.production import Production

        if isinstance(value, Production):
            self._production = value.value
        elif isinstance(value, (int, float)):
            self._production = value
        elif isinstance(value, Yields):
            self._production = value.production.value

    @property
    def science(self) -> "BaseResource":
        from gameplay.resources.core.basic.science import Science

        return Science(value=self._science)

    @science.setter
    def science(self, value: "float | Yields | Science") -> None:
        from gameplay.resources.core.basic.science import Science

        if isinstance(value, Science):
            self._science = value.value
        elif isinstance(value, (int, float)):
            self._science = value
        elif isinstance(value, Yields):
            self._science = value.science.value

    @property
    def food(self) -> "BaseResource":
        from gameplay.resources.core.basic.food import Food

        return Food(value=self._food)

    @food.setter
    def food(self, value: "float | Yields | Food") -> None:
        from gameplay.resources.core.basic.food import Food

        if isinstance(value, Food):
            self._food = value.value
        elif isinstance(value, (int, float)):
            self._food = value
        elif isinstance(value, Yields):
            self._food = value.food.value

    @property
    def culture(self) -> "BaseResource":
        from gameplay.resources.core.basic.culture import Culture

        return Culture(value=self._culture)

    @culture.setter
    def culture(self, value: "float | Yields | Culture") -> None:
        from gameplay.resources.core.basic.culture import Culture

        if isinstance(value, Culture):
            self._culture = value.value
        elif isinstance(value, (int, float)):
            self._culture = value
        elif isinstance(value, Yields):
            self._culture = value.culture.value

    @property
    def housing(self) -> "BaseResource":
        from gameplay.resources.core.basic.housing import Housing

        return Housing(value=self._housing)

    @housing.setter
    def housing(self, value: "float | Yields | Housing") -> None:
        from gameplay.resources.core.basic.housing import Housing

        if isinstance(value, Housing):
            self._housing = value.value
        elif isinstance(value, (int, float)):
            self._housing = value
        elif isinstance(value, Yields):
            self._housing = value.housing.value

    @property
    def faith(self) -> "BaseResource":
        from gameplay.resources.core.basic.faith import Faith

        return Faith(value=self._faith)

    @faith.setter
    def faith(self, value: "float | Yields | Faith") -> None:
        from gameplay.resources.core.basic.faith import Faith

        if isinstance(value, Faith):
            self._faith = value.value
        elif isinstance(value, (int, float)):
            self._faith = value
        elif isinstance(value, Yields):
            self._faith = value.faith.value

    def clone(self) -> "Yields":
        # Create a deep copy of the TileYield instance.
        return copy.deepcopy(self)

    def total_value(self) -> float:
        # Sum the .value of each calculatable property.
        return sum(getattr(self, prop).value for prop in self.calculatable_properties())

    def __repr__(self) -> str:
        return (
            f"TileYield<Mode:{self.MODE_STR[self.mode]}>"
            f"g:<{self.gold}>|p:<{self.production}>|s:<{self.science}>|"
            f"f:<{self.food}>|c:<{self.culture}>|h:<{self.housing}>|fa:<{self.faith}>"
        )

    def __add__(self, b: "Yields") -> Self:
        return self.add(tile_yield=b)

    def __mul__(self, b: "Yields") -> Self:
        return self.multiply(tile_yield=b)

    def __sub__(self, b: "Yields") -> Self:
        return self.subtract(tile_yield=b)

    def __truediv__(self, b: "Yields") -> Self:
        return self.divide(tile_yield=b)

    def add(self, tile_yield: "Yields") -> Self:
        # Process simple calculatable properties
        for prop in self.calculatable_properties():
            current = getattr(self, prop)
            addition = getattr(tile_yield, prop)
            new_val = current + addition
            setattr(self, prop, new_val)

        # Process mechanic resources similarly
        # for prop in self.mechanic_resources():
        # current = getattr(self, prop)
        # addition = getattr(tile_yield, prop)
        # new_val = current.value + addition.value
        # setattr(self, prop, type(current)(value=new_val))

        # Process great people yields
        # for prop in self.calculatable_great_people():
        # current = getattr(self, f"great_person_{prop}")
        # addition = getattr(tile_yield, f"great_person_{prop}")
        # new_val = current.value + addition.value
        # setattr(self, f"great_person_{prop}", type(current)(value=new_val))

        return self

    def multiply(self, tile_yield: "Yields") -> Self:
        # Multiply calculatable properties
        for prop in self.calculatable_properties():
            multiplicative = getattr(tile_yield, prop)
            if multiplicative.value in {0.0, 1.0, -1.0}:
                continue
            current = getattr(self, prop)
            new_val = current.value * multiplicative.value
            setattr(self, prop, type(current)(value=new_val))

        """Multiply mechanic resources
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
            setattr(self, f"great_person_{prop}", type(current)(value=new_val))"""

        return self

    def subtract(self, tile_yield: "Yields") -> Self:
        # Process simple calculatable properties
        for prop in self.calculatable_properties():
            current = getattr(self, prop)
            subtraction = getattr(tile_yield, prop)
            new_val = current.value - subtraction.value
            setattr(self, prop, type(current)(value=new_val))
        # Process mechanic resources similarly
        """ for prop in self.mechanic_resources():
            current = getattr(self, prop)
            subtraction = getattr(tile_yield, prop)
            new_val = current.value - subtraction.value
            setattr(self, prop, type(current)(value=new_val))
        # Process great people yields
        for prop in self.calculatable_great_people():
            current = getattr(self, f"great_person_{prop}")
            subtraction = getattr(tile_yield, f"great_person_{prop}")
            new_val = current.value - subtraction.value
            setattr(self, f"great_person_{prop}", type(current)(value=new_val))"""
        return self

    def divide(self, tile_yield: "Yields") -> Self:
        # Process simple calculatable properties
        for prop in self.calculatable_properties():
            divisor = getattr(tile_yield, prop)
            # Skip division for values that don't modify the yield or could be zero.
            if divisor.value in {0.0, 1.0, -1.0}:
                continue
            current = getattr(self, prop)
            new_val = current.value / divisor.value
            setattr(self, prop, type(current)(value=new_val))
        """ # Process mechanic resources similarly
        for prop in self.mechanic_resources():
            divisor = getattr(tile_yield, prop)
            if divisor.value in {0.0, 1.0, -1.0}:
                continue
            current = getattr(self, prop)
            new_val = current.value / divisor.value
            setattr(self, prop, type(current)(value=new_val))
        # Process great people yields
        for prop in self.calculatable_great_people():
            divisor = getattr(tile_yield, f"great_person_{prop}")
            if divisor.value in {0.0, 1.0, -1.0}:
                continue
            current = getattr(self, f"great_person_{prop}")
            new_val = current.value / divisor.value
            setattr(self, f"great_person_{prop}", type(current)(value=new_val))"""
        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() == other.total_value()

    def __gt__(self, other: "Yields") -> bool:
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() > other.total_value()

    def __lt__(self, other: "Yields") -> bool:
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() < other.total_value()

    def __ge__(self, other: "Yields") -> bool:
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() >= other.total_value()

    def __le__(self, other: "Yields") -> bool:
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() <= other.total_value()

    def __ne__(self, other: "Yields") -> bool:  # type: ignore
        if not isinstance(other, Yields):
            return NotImplemented
        return self.total_value() != other.total_value()

    # Reverse arithmetic operators (clone to avoid modifying the left-hand operand)
    def __radd__(self, other: "Yields") -> "Yields":
        if not isinstance(other, Yields):
            return NotImplemented
        return other.clone().add(self)

    def __rsub__(self, other: "Yields") -> "Yields":
        if not isinstance(other, Yields):
            return NotImplemented
        return other.clone().subtract(self)

    def __rmul__(self, other: "Yields") -> "Yields":
        if not isinstance(other, Yields):
            return NotImplemented
        return other.clone().multiply(self)

    def __rtruediv__(self, other: "Yields") -> "Yields":
        if not isinstance(other, Yields):
            return NotImplemented
        return other.clone().divide(self)

    def set_prop(self, name: str, value: Any):
        if name in self.calculatable_great_people() + self.calculatable_properties():
            raise ValueError(f"cannot set property[{name}] as it does not exist or is accessible")
        setattr(self, name, value)

    def get_prop(self, name: str) -> Any:
        if name not in self.calculatable_great_people() + self.calculatable_properties():
            raise ValueError(f"cannot get property[{name}] as it does not exist or is accessible")
        return getattr(self, name)

    def toDict(self, only_non_null: bool = False) -> Dict[str, Any]:
        return {
            "gold": self.gold,
            "production": self.production,
            "science": self.science,
            "food": self.food,
            "culture": self.culture,
            "housing": self.housing,
            "faith": self.faith,
            "contentment": self._contentment,
            "angre": self._angre,
            "revolt": self._revolt,
            "stability": self._stability,
            "great_person_science": self._great_person_science,
            "great_person_production": self._great_person_production,
            "great_person_artist": self._great_person_artist,
            "great_person_military": self._great_person_military,
            "great_person_commerce": self._great_person_commerce,
            "great_person_hero": self._great_person_hero,
            "great_person_holy": self._great_person_holy,
        }

    def export_basic(self) -> List["BaseResource"]:
        resources: List["BaseResource"] = [
            self.gold,
            self.production,
            self.food,
            self.science,
            self.culture,
        ]
        return resources

    # Calculate final yield based on a base yield (self) and optional modifiers.
    # For each calculatable property, the final yield is:
    #   final = round((base + additive) * (1 + percentage_add) * (1 + percentage_cum))
    # This method modifies self in place.
    def calculate(
        self,
        additive: "Yields | None" = None,
        percentage_add: "Yields | None" = None,
        percentage_cum: "Yields | None" = None,
    ) -> None:
        # Use null yields if modifiers aren't provided.
        additive = additive or Yields.nullYield()
        percentage_add = percentage_add or Yields.nullYield()
        percentage_cum = percentage_cum or Yields.nullYield()

        for prop in self.calculatable_properties():
            base_val = getattr(self, prop).value
            add_val = getattr(additive, prop).value
            percentage_add_val = getattr(percentage_add, prop).value
            percentage_cum_val = getattr(percentage_cum, prop).value
            # Combine values: negative additive will subtract, negative percentages reduce yield.
            final_val = (base_val + add_val) * (1 + percentage_add_val) * (1 + percentage_cum_val)
            # Round final yield as yields should be integers.
            final_val = round(final_val)
            current = getattr(self, prop)
            setattr(self, prop, type(current)(value=final_val))

    def props(self, only_non_nul: bool = False) -> Dict[Any, Any]:
        a: Dict[Any, Any] = {}
        for item in self.calculatable_properties():
            attr = getattr(self, item)
            if only_non_nul and attr.value == 0.0:
                continue
            a[item] = attr
        return a

    def only(self, only: List[str]) -> "Yields":
        # Create a new instance with zeroed yields.
        new_tile_yield: "Yields" = self.nullYield()

        # Update the internal lists to only include the requested properties.
        new_tile_yield._calculatable_properties = [prop for prop in self._calculatable_properties if prop in only]
        new_tile_yield._mechanic_resources = [prop for prop in self._mechanic_resources if prop in only]
        new_tile_yield._calculatable_great_people = [prop for prop in self._calculatable_great_people if prop in only]

        # Copy over the specified properties.
        for prop in only:
            if prop in self._calculatable_properties:
                setattr(new_tile_yield, prop, copy.deepcopy(getattr(self, prop)))
            elif prop in self._mechanic_resources:
                setattr(new_tile_yield, prop, copy.deepcopy(getattr(self, prop)))
            elif prop in self._calculatable_great_people:
                # For great people yields, the actual attribute is prefixed with 'great_person_'.
                setattr(new_tile_yield, f"great_person_{prop}", copy.deepcopy(getattr(self, f"great_person_{prop}")))
            else:
                raise ValueError(f"Property {prop} is not recognized")
        return new_tile_yield

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
    def baseYield() -> "Yields":
        return Yields()

    @staticmethod
    def nullYield() -> "Yields":
        return Yields(gold=0.0, production=0.0, science=0.0, food=0.0, culture=0.0, housing=0.0, faith=0.0)

    def __str__(self) -> str:
        return (
            f"g:{self.gold.value}|p:{self.production.value}|s:{self.science.value}|"
            f"f:{self.food.value}|c:{self.culture.value}|h:{self.housing.value}|fa:{self.faith.value}"
        )

    def __len__(self) -> int:
        total = 0
        for property in self.calculatable_properties():
            total += getattr(self, property)
        return int(total)
