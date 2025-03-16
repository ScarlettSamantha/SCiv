from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Self, Tuple, Type, TypeVar, Union

from exceptions.resource_exception import ResourceTypeException
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStr, t_


class ResourceType(Enum):
    MECHANIC = -1
    BASIC = 0
    BONUS = 1
    STRATEGIC = 2
    LUXURY = 3


class ResourceValueType(Enum):
    FLOAT = 0
    INT = 1


class ResourceTypeBase:
    def __init__(
        self,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        type_: ResourceType,
    ):
        self.type_name: T_TranslationOrStr = name
        self.type_description: T_TranslationOrStr = description
        self.type_num: ResourceType = type_


class ResourceTypeMechanic(ResourceTypeBase):
    def __init__(self) -> None:
        super().__init__(
            name=t_("content.resources.core.types.mechanic.name"),
            description=t_("content.resources.core.types.mechanic.description"),
            type_=ResourceType.MECHANIC,
        )


class ResourceTypeBonus(ResourceTypeBase):
    def __init__(self) -> None:
        super().__init__(
            name=t_("content.resources.core.types.bonus.name"),
            description=t_("content.resources.core.types.bonus.description"),
            type_=ResourceType.BONUS,
        )


class ResourceTypeStrategic(ResourceTypeBase):
    def __init__(self) -> None:
        super().__init__(
            t_("content.resources.core.types.strategic.name"),
            t_("content.resources.core.types.strategic.description"),
            ResourceType.STRATEGIC,
        )


class ResourceTypeLuxury(ResourceTypeBase):
    def __init__(self) -> None:
        super().__init__(
            name=t_("content.resources.core.types.luxury.name"),
            description=t_("content.resources.core.types.luxury.description"),
            type_=ResourceType.LUXURY,
        )


class ResourceTypeBasic(ResourceTypeBase):
    def __init__(self):
        super().__init__(
            name=t_("content.resources.core.types.basic.name"),
            description=t_("content.resources.core.types.basic.description"),
            type_=ResourceType.BASIC,
        )


T_ResourceType = TypeVar("T_ResourceType", bound=ResourceTypeBase)
T_ResourceTypeType = TypeVar("T_ResourceTypeType", bound=Type[ResourceTypeBase])


class ResourceSpawnablePlace(Enum):
    LAND = 0
    WATER = 1
    BOTH = 2


class BaseResource(Generic[T_ResourceType]):
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    type: Type[T_ResourceType]
    icon: str = "assets/icons/resources/default.png"
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    spawn_type: ResourceSpawnablePlace = ResourceSpawnablePlace.LAND

    # Determines the chance that the resource will spawn on a given tile. If a tuple is provided (min, max),
    # If given a dict with terrains, the spawn chance will be different for each terrain.
    # If it is a baseTerrain object, the spawn chance will be the same for all terrains.
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0.0

    # Determines the amount of the resource that will spawn on a given tile. If a tuple is provided (min, max),
    # the amount will be randomly chosen within this range.
    # These are percentages of the total amount of the resource that can be found on the map.
    spawn_amount: float | Tuple[float, float] = 1.0

    # Determines if the resource can form clusters. If None, the resource will not be clusterable.
    # If a float value is provided, it represents the probability (0.0 to 1.0) that a neighboring tile
    # will also contain the resource. A value of 0.0 means no clustering (isolated occurrences), while
    # a value of 1.0 ensures that all adjacent tiles will contain the resource.
    #
    # Clustering works by selecting a central tile and then checking adjacent tiles for inclusion
    # based on this probability. This process continues outward until the maximum radius is reached.
    clusterable: float | None = None

    # Defines the maximum radius for clustering. If set to 1, the resource can only appear on directly
    # adjacent tiles. If set to 2, the cluster can expand up to two tiles away, and so on.
    # Has no effect if `clusterable` is None.
    cluster_max_radius: int | Tuple[int, int] = (1, 2)

    # Determines the dropoff rate of clustering probability as the distance from the center tile increases.
    # A value of 1.0 means that the probability decreases linearly by 1 per unit of distance.
    # If a tuple is provided (min, max), the dropoff rate will be randomly chosen within this range.
    # Has no effect if `clusterable` is None.
    cluster_dropoff_amount_rate: float | Tuple[float, float] = (0.5, 1.0)

    def __init__(
        self,
        value: Union[float, int] = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.value: Union[float, int] = value
        self.value_storage: ResourceValueType = self.configure_as_float_or_int
        self._tile_yield_modifier: Yields = Yields.nullYield()

    def get_yield_modifier(self) -> "Yields":
        return self._tile_yield_modifier  # type: ignore # Pyright is wrong here. It is not None. its in the setup method.

    def add_to_yield_modifier(self, yields: "Yields") -> None:
        self._tile_yield_modifier.add(yields)  # type: ignore # Pyright is wrong here. It is not None. its in the setup method.

    def _check_same_type(self, other: "BaseResource") -> None:
        if not isinstance(other, BaseResource) or type(self) != type(other):
            raise TypeError(
                f"Operation not supported between instances of {type(self).__name__} and {type(other).__name__}"
            )

    # Overloaded operators
    def __add__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value + other.value
        return self.value + other

    def __radd__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        return self.__add__(other)

    def __sub__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value - other.value
        return self.value - other

    def __rsub__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return other.value - self.value
        return other - self.value

    def __mul__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value * other.value
        return self.value * other

    def __rmul__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        return self.__mul__(other)

    def __truediv__(self, other: Union["BaseResource", float, int]) -> float:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value / other.value
        return self.value / other

    def __rtruediv__(self, other: Union["BaseResource", float, int]) -> float:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return other.value / self.value
        return other / self.value

    def __floordiv__(self, other: Union["BaseResource", float, int]) -> int:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return int(self.value // other.value)
        return int(self.value // other)

    def __rfloordiv__(self, other: Union["BaseResource", float, int]) -> int:
        return self.__floordiv__(other)

    def __mod__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value % other.value
        return self.value % other

    def __rmod__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        return self.__mod__(other)

    def __pow__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        if isinstance(other, BaseResource):
            self._check_same_type(other)
            return self.value**other.value
        return self.value**other

    def __rpow__(self, other: Union["BaseResource", float, int]) -> Union[float, int]:
        return self.__pow__(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, "BaseResource"):
            return self.value == other.value
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Union["BaseResource", float, int]) -> bool:
        if isinstance(other, BaseResource):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Union["BaseResource", float, int]) -> bool:
        if isinstance(other, BaseResource):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Union["BaseResource", float, int]) -> bool:
        if isinstance(other, BaseResource):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Union["BaseResource", float, int]) -> bool:
        if isinstance(other, BaseResource):
            return self.value >= other.value
        return self.value >= other

    def __repr__(self) -> str:
        return f"{self.key}: {self.value}"

    @classmethod
    def strategic(cls, *args: Any, **kwargs: Any) -> "BaseResource":
        return cls(*args, **kwargs, type_=ResourceTypeStrategic)

    @classmethod
    def luxury(cls, *args: Any, **kwargs: Any) -> "BaseResource":
        return cls(*args, **kwargs, type_=ResourceTypeLuxury)

    @classmethod
    def bonus(cls, *args: Any, **kwargs: Any) -> "BaseResource":
        return cls(*args, **kwargs, type_=ResourceTypeBonus)

    @classmethod
    def basic(cls, *args: Any, **kwargs: Any) -> "BaseResource":
        return cls(*args, **kwargs, type_=ResourceTypeBasic)

    @classmethod
    def mechanic(cls, *args: Any, **kwargs: Any) -> "BaseResource":
        return cls(*args, **kwargs, type_=ResourceTypeMechanic)


mapping: Dict[ResourceType, Type[ResourceTypeBase]] = {
    ResourceType.MECHANIC: ResourceTypeMechanic,
    ResourceType.BASIC: ResourceTypeBasic,
    ResourceType.BONUS: ResourceTypeBonus,
    ResourceType.STRATEGIC: ResourceTypeStrategic,
    ResourceType.LUXURY: ResourceTypeLuxury,
}

# Inverted mapping to allow lookup by ResourceTypeBase
inverted_mapping: Dict[Type[ResourceTypeBase], ResourceType] = {v: k for k, v in mapping.items()}


class Resources:
    def __init__(self):
        self.resources: Dict[Type[ResourceTypeBase], Dict[str, BaseResource]] = {}
        self.define_types()

    def define_types(self) -> None:
        global mapping
        for item in mapping.values():
            if item not in self.resources.keys():
                self.resources[item] = {}

    def flatten(self, types: List[ResourceType] = []) -> Dict[str, BaseResource]:
        if types:
            return {
                key: resource
                for sub_dict in [self.resources[mapping[t]] for t in types if mapping[t] in self.resources]
                for key, resource in sub_dict.items()
            }
        return {key: resource for sub_dict in self.resources.values() for key, resource in sub_dict.items()}

    def flatten_non_mechanic(self) -> Dict[str, BaseResource]:
        # This is a helper method to get all resources that are not mechanic resources.
        # Also to counter the issue of circular imports.
        return self.flatten([ResourceType.BONUS, ResourceType.LUXURY, ResourceType.STRATEGIC])

    def flatten_basics(self) -> Dict[str, BaseResource]:
        # This is a helper method to get all resources that are not mechanic resources.
        # Also to counter the issue of circular imports.
        return self.resources[ResourceTypeBasic]

    def get(
        self, _type: Type[ResourceTypeBase] | None = None, key: str | None = None
    ) -> Dict[Type[ResourceTypeBase], Dict[str, BaseResource]] | BaseResource | Dict[str, BaseResource]:
        if _type is None:
            for sub_dict in self.resources.values():
                for resource in sub_dict.values():
                    if resource.key == key:
                        return resource
                raise KeyError(f"Key {key} not found in resources")
        else:
            sub: Dict[str, BaseResource] = self.resources[_type]
            if key is not None:
                if key not in sub:
                    raise KeyError(f"Key {key} not found in resources")
                return sub[key]
        return self.resources

    def toDict(self) -> Dict[Type[ResourceTypeBase], Dict[str, BaseResource]]:
        return self.resources

    def add(self, resource: Union[BaseResource, List[BaseResource]], auto_instance: bool = True) -> None:
        def _add(self: Self, tmp_resource: BaseResource) -> None:
            resource_type: Type[ResourceTypeBase] = tmp_resource.type
            if resource_type not in self.resources:
                self.resources[resource_type] = {}
            self.resources[resource_type][tmp_resource.key] = tmp_resource

        if isinstance(resource, BaseResource):
            _add(self=self, tmp_resource=resource)
        elif isinstance(resource, list):  # type: ignore | Pyright is wrong here. Its saying that its a un-needed check but it is needed because it can also be anything else.
            for r in resource:
                _add(self=self, tmp_resource=r)
        else:
            raise ResourceTypeException(f"Resource must be of type Resource, not {type(resource)}")

    def remove(self, resource: BaseResource) -> None:
        resource_type: Type[ResourceTypeBase] = resource.type
        if resource_type in self.resources and resource.key in self.resources[resource_type]:
            del self.resources[resource_type][resource.key]

    def has(self, resource: Optional[BaseResource] = None) -> bool:
        if resource is None:
            return bool(self.resources)
        return resource.key in self.resources[resource.type]

    def __add__(self, b: BaseResource) -> None:
        self.add(b)

    def __getitem__(self, key: str) -> Dict[str, BaseResource] | BaseResource:
        return self.flatten()[key]

    def __len__(self) -> int:
        """This is the true len for check if there is anything in the resources"""
        return len(self.flatten())

    def len(self) -> int:
        """This is the len that checks if there is anything actually valuable in the resources and non mechanic resources."""
        return len(self.flatten([ResourceType.BONUS, ResourceType.LUXURY, ResourceType.STRATEGIC]))


class Costs:
    def __init__(self, costs: List[BaseResource] | BaseResource) -> None:
        self.costs: List[BaseResource] = costs if isinstance(costs, list) else [costs]
