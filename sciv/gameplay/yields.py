import copy
from typing import TYPE_CHECKING, Any, Dict, List, Self, Type

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

    _calculatable_properties: List[str] = [
        "gold",
        "production",
        "science",
        "food",
        "culture",
        "housing",
        "faith",
    ]

    _mechanic_resources: List[str] = ["contentment", "angre", "revolt", "stability"]

    _calculatable_great_people: List[str] = [
        "science",
        "production",
        "artist",
        "military",
        "commerce",
        "hero",
        "holy",
    ]

    _RES_CACHE: Dict[str, Type["BaseResource"]] | None = None

    @classmethod
    def _res_cache(cls) -> Dict[str, Type["BaseResource"]]:
        if cls._RES_CACHE is None:
            from gameplay.resources.core.basic.culture import Culture  # type: ignore
            from gameplay.resources.core.basic.faith import Faith  # type: ignore
            from gameplay.resources.core.basic.food import Food  # type: ignore
            from gameplay.resources.core.basic.gold import Gold  # type: ignore
            from gameplay.resources.core.basic.housing import Housing  # type: ignore
            from gameplay.resources.core.basic.production import Production  # type: ignore
            from gameplay.resources.core.basic.science import Science  # type: ignore

            cls._RES_CACHE = {
                "gold": Gold,
                "production": Production,
                "science": Science,
                "food": Food,
                "culture": Culture,
                "housing": Housing,
                "faith": Faith,
            }
        return cls._RES_CACHE

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

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        for prop in self.calculatable_properties() + self.mechanic_resources():
            key = f"_{prop}"
            if key in state and (state[key] is None or state[key] == 0.0):
                del state[key]
        for prop in self._calculatable_great_people:
            key = f"_great_person_{prop}"
            if key in state and (state[key] is None or state[key] == 0.0):
                del state[key]
        return state

    def get_copy(self) -> "Yields":
        return Yields(
            name=self._name,
            gold=self._gold,
            production=self._production,
            science=self._science,
            food=self._food,
            culture=self._culture,
            housing=self._housing,
            faith=self._faith,
            mode=self.mode,
        )

    def dump(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        for key, val in list(self.__dict__.items()):
            if val is None or val == 0.0:
                state.pop(key, None)
        return state

    def load_state(self, state: Dict[str, Any]) -> None:
        self._name = state.get("_name", None)
        self.mode = state.get("mode", self.ADDITIVE)
        for prop in self.calculatable_properties():
            setattr(self, f"_{prop}", state.get(f"_{prop}", 0.0))
        for prop in self.mechanic_resources():
            setattr(self, f"_{prop}", state.get(f"_{prop}", 0.0))
        for prop in self._calculatable_great_people:
            setattr(self, f"_great_person_{prop}", state.get(f"_great_person_{prop}", 0.0))

    @property
    def name(self) -> None | str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def gold(self) -> "BaseResource":
        cls = self._res_cache()["gold"]
        return cls(value=self._gold)

    @gold.setter
    def gold(self, value: "float | Yields | Gold") -> None:
        if isinstance(value, Yields):
            self._gold = value._gold
        elif hasattr(value, "value"):
            self._gold = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._gold = value  # type: ignore[assignment]

    @property
    def production(self) -> "BaseResource":
        cls = self._res_cache()["production"]
        return cls(value=self._production)

    @production.setter
    def production(self, value: "float | Yields | Production") -> None:
        if isinstance(value, Yields):
            self._production = value._production
        elif hasattr(value, "value"):
            self._production = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._production = value  # type: ignore[assignment]

    @property
    def science(self) -> "BaseResource":
        cls = self._res_cache()["science"]
        return cls(value=self._science)

    @science.setter
    def science(self, value: "float | Yields | Science") -> None:
        if isinstance(value, Yields):
            self._science = value._science
        elif hasattr(value, "value"):
            self._science = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._science = value  # type: ignore[assignment]

    @property
    def food(self) -> "BaseResource":
        cls = self._res_cache()["food"]
        return cls(value=self._food)

    @food.setter
    def food(self, value: "float | Yields | Food") -> None:
        if isinstance(value, Yields):
            self._food = value._food
        elif hasattr(value, "value"):
            self._food = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._food = value  # type: ignore[assignment]

    @property
    def culture(self) -> "BaseResource":
        cls = self._res_cache()["culture"]
        return cls(value=self._culture)

    @culture.setter
    def culture(self, value: "float | Yields | Culture") -> None:
        if isinstance(value, Yields):
            self._culture = value._culture
        elif hasattr(value, "value"):
            self._culture = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._culture = value  # type: ignore[assignment]

    @property
    def housing(self) -> "BaseResource":
        cls = self._res_cache()["housing"]
        return cls(value=self._housing)

    @housing.setter
    def housing(self, value: "float | Yields | Housing") -> None:
        if isinstance(value, Yields):
            self._housing = value._housing
        elif hasattr(value, "value"):
            self._housing = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._housing = value  # type: ignore[assignment]

    @property
    def faith(self) -> "BaseResource":
        cls = self._res_cache()["faith"]
        return cls(value=self._faith)

    @faith.setter
    def faith(self, value: "float | Yields | Faith") -> None:
        if isinstance(value, Yields):
            self._faith = value._faith
        elif hasattr(value, "value"):
            self._faith = getattr(value, "value")  # type: ignore[attr-defined]
        else:
            self._faith = value  # type: ignore[assignment]

    def clone(self) -> "Yields":
        return copy.deepcopy(self)

    def total_value(self) -> int:
        return int(
            float(self._gold)
            + float(self._production)
            + float(self._science)
            + float(self._food)
            + float(self._culture)
            + float(self._housing)
            + float(self._faith)
        )

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
        for prop in self.calculatable_properties():
            setattr(self, f"_{prop}", float(getattr(self, f"_{prop}")) + float(getattr(tile_yield, f"_{prop}")))
        return self

    def multiply(self, tile_yield: "Yields") -> Self:
        for prop in self.calculatable_properties():
            m = float(getattr(tile_yield, f"_{prop}"))
            if m in {0.0, 1.0, -1.0}:
                continue
            cur = float(getattr(self, f"_{prop}"))
            setattr(self, f"_{prop}", cur * m)
        return self

    def subtract(self, tile_yield: "Yields") -> Self:
        for prop in self.calculatable_properties():
            setattr(self, f"_{prop}", float(getattr(self, f"_{prop}")) - float(getattr(tile_yield, f"_{prop}")))
        return self

    def divide(self, tile_yield: "Yields") -> Self:
        for prop in self.calculatable_properties():
            d = float(getattr(tile_yield, f"_{prop}"))
            if d in {0.0, 1.0, -1.0}:
                continue
            cur = float(getattr(self, f"_{prop}"))
            setattr(self, f"_{prop}", cur / d)
        return self

    def __eq__(self, other: "Yields | object") -> bool:
        if not isinstance(other, Yields):
            return False
        return self.total_value() == other.total_value()

    def __gt__(self, other: "Yields") -> bool:
        return self.total_value() > other.total_value()

    def __lt__(self, other: "Yields") -> bool:
        return self.total_value() < other.total_value()

    def __ge__(self, other: "Yields") -> bool:
        return self.total_value() >= other.total_value()

    def __le__(self, other: "Yields") -> bool:
        return self.total_value() <= other.total_value()

    def __ne__(self, other: "Yields") -> bool:  # type: ignore
        return self.total_value() != other.total_value()

    def __radd__(self, other: "Yields") -> "Yields":
        return other.clone().add(self)

    def __rsub__(self, other: "Yields") -> "Yields":
        return other.clone().subtract(self)

    def __rmul__(self, other: "Yields") -> "Yields":
        return other.clone().multiply(self)

    def __rtruediv__(self, other: "Yields") -> "Yields":
        return other.clone().divide(self)

    def set_prop(self, name: str, value: Any) -> None:
        if name not in self.calculatable_great_people() + self.calculatable_properties():
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

    def on_inspect(self, basic: bool = False) -> Dict[str, str]:
        data: Dict[str, str] = {
            "gold": str(float(self._gold)),
            "production": str(float(self._production)),
            "science": str(float(self._science)),
            "food": str(float(self._food)),
            "culture": str(float(self._culture)),
            "housing": str(float(self._housing)),
            "faith": str(float(self._faith)),
        }
        if basic is True:
            return data

        data.update(
            {
                "contentment": str(self._contentment),
                "angre": str(self._angre),
                "revolt": str(self._revolt),
                "stability": str(self._stability),
            }
        )
        return data

    def export_basic(self) -> List["BaseResource"]:
        return [self.gold, self.production, self.food, self.science, self.culture, self.faith]

    def calculate(
        self,
        additive: "Yields | None" = None,
        percentage_add: "Yields | None" = None,
        percentage_cum: "Yields | None" = None,
    ) -> None:
        for prop in self.calculatable_properties():
            base_val = float(getattr(self, f"_{prop}"))
            add_val = float(getattr(additive, f"_{prop}")) if isinstance(additive, Yields) else 0.0
            pad = float(getattr(percentage_add, f"_{prop}")) if isinstance(percentage_add, Yields) else 0.0
            pcum = float(getattr(percentage_cum, f"_{prop}")) if isinstance(percentage_cum, Yields) else 0.0
            final_val = round((base_val + add_val) * (1.0 + pad) * (1.0 + pcum))
            setattr(self, f"_{prop}", final_val)

    def props(self, only_non_nul: bool = False) -> Dict[str, Any]:
        a: Dict[str, Any] = {}
        for item in self.calculatable_properties():
            if only_non_nul and float(getattr(self, f"_{item}")) == 0.0:
                continue
            a[item] = getattr(self, item)
        return a

    def only(self, only: List[str]) -> "Yields":
        new_tile_yield: "Yields" = self.nullYield()
        new_tile_yield._calculatable_properties = [prop for prop in self._calculatable_properties if prop in only]
        new_tile_yield._mechanic_resources = [prop for prop in self._mechanic_resources if prop in only]
        new_tile_yield._calculatable_great_people = [prop for prop in self._calculatable_great_people if prop in only]
        for prop in only:
            if prop in self._calculatable_properties:
                setattr(new_tile_yield, f"_{prop}", float(getattr(self, f"_{prop}")))
            elif prop in self._mechanic_resources:
                setattr(new_tile_yield, f"_{prop}", float(getattr(self, f"_{prop}")))
            elif prop in self._calculatable_great_people:
                gp = f"_great_person_{prop}"
                setattr(new_tile_yield, gp, float(getattr(self, gp)))
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
            f"g:{float(self._gold)}|p:{float(self._production)}|s:{float(self._science)}|"
            f"f:{float(self._food)}|c:{float(self._culture)}|h:{float(self._housing)}|fa:{float(self._faith)}"
        )

    def __len__(self) -> int:
        total = 0.0
        for prop in self.calculatable_properties():
            total += float(getattr(self, f"_{prop}"))
        return int(total)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Yields":
        instance = cls()
        for key, value in data.items():
            if key == "mode":
                instance.mode = int(value)
                continue
            if key == "_name" or key == "name":
                instance._name = value
                continue
            if key in instance._calculatable_properties:
                setattr(instance, f"_{key}", float(value))
                continue
            if key in instance._mechanic_resources:
                setattr(instance, f"_{key}", float(value))
                continue
            if key.startswith("great_person_"):
                setattr(instance, f"_{key}", float(value))
                continue
            if key.startswith("_") and hasattr(instance, key):
                setattr(instance, key, value)
                continue
            raise ValueError(f"Property {key} does not exist in Yields class.")
        return instance
