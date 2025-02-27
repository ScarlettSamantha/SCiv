from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic
from data.tiles.tile import Tile
from mixins.singleton import Singleton
from enum import Enum
from uuid import uuid4

from gameplay.units.classes._base import UnitBaseClass
from gameplay.improvements import Improvement
from gameplay.city import City
from gameplay.player import Player
from system.entity import BaseEntity

from weakref import ReferenceType, ref


class EntityType(Enum):
    TILE = ("_tiles_", Tile)
    UNIT = ("_units_", UnitBaseClass)
    IMPROVEMENT = ("_improvements_", Improvement)
    CITY = ("_cities_", City)
    PLAYER = ("_players_", Player)

    def __init__(self, storage_key: str, base_type: Type[BaseEntity]):
        self.storage_key = storage_key
        self.base_type = base_type


K = TypeVar("K", bound=str)
V = TypeVar("V", bound=BaseEntity)


class EntityManager(Singleton):
    _entities: Dict[EntityType, Dict[str, BaseEntity]] = {type_: {} for type_ in EntityType}

    def __init__(self):
        self.serializer: Optional[BaseEntityManagerSerializer] = None

    def __setup__(self, base, serializer: Type["BaseEntityManagerSerializer"], *args, **kwargs):
        self.base = base
        self.serializer = serializer()
        return super().__setup__(*args, **kwargs)

    def check_object_against_type(self, type: EntityType, entity: object) -> bool:
        return isinstance(entity, type.base_type)

    def object_type_to_storage(self, type: EntityType) -> Dict[str, BaseEntity]:
        return self._entities[type]

    def register(self, type: EntityType, entity: BaseEntity, key: str = str(uuid4().hex), inject_key: bool = True):
        if not self.check_object_against_type(type, entity):
            raise TypeError(f"Entity does not match expected type {type.base_type}")

        storage = self.object_type_to_storage(type)
        if key in storage:
            raise ValueError(f"Entity with key {key} already exists.")

        if inject_key:
            entity.entity_key = key
        storage[key] = entity

    def unregister(self, type: EntityType, key: str):
        self.object_type_to_storage(type).pop(key, None)

    def add_library(self, type: EntityType):
        if type not in self._entities:
            self._entities[type] = {}

    def get_ref(
        self, type: EntityType, key: str, weak_ref: bool = False
    ) -> BaseEntity | ReferenceType[BaseEntity] | None:
        storage = self.object_type_to_storage(type)
        entity = storage.get(key)
        return ref(entity) if weak_ref and entity else entity

    def get(self, type: EntityType, key: str) -> BaseEntity | None:
        result = self.get_ref(type, key, weak_ref=False)
        if not isinstance(result, BaseEntity):
            raise AssertionError("Weak reference is not supported in get(), use get_ref() with weak_ref=True")
        return result

    def has(self, type: EntityType, key: str) -> bool:
        return key in self.object_type_to_storage(type)

    def get_multiple(
        self, type: EntityType, keys: list[str], weak_refs: bool = False
    ) -> list[BaseEntity | ReferenceType[BaseEntity] | None]:
        return [self.get_ref(type, key, weak_ref=weak_refs) for key in keys]

    def get_all(self, type: Optional[EntityType] = None) -> Dict[str, BaseEntity]:
        if type is None:
            return {key: entity for storage in self._entities.values() for key, entity in storage.items()}
        return self.object_type_to_storage(type)

    def get_all_refs(self, type: EntityType) -> Dict[str, ReferenceType[BaseEntity]]:
        return {k: ref(v) for k, v in self.object_type_to_storage(type).items()}

    def get_all_keys(self, type: EntityType) -> list[str]:
        return list(self.object_type_to_storage(type).keys())

    def clear(self, type: Optional[EntityType] = None):
        if type:
            self.object_type_to_storage(type).clear()
        else:
            for storage in self._entities.values():
                storage.clear()

    def register_serializer(self, serializer: "BaseEntityManagerSerializer"):
        self.serializer = serializer

    def dump(self, type: Optional[EntityType] = None):
        if not self.serializer:
            raise ValueError("No serializer registered.")
        self.serializer.dump(self.get_all(type))

    def load(self, data: Any, type: Optional[EntityType] = None):
        if not self.serializer:
            raise ValueError("No serializer registered.")

        self.clear(type)
        loaded_data = self.serializer.load(data)

        for entity_type in EntityType:
            entity_dict = loaded_data.get(entity_type.storage_key, {})
            if isinstance(entity_dict, dict):
                self._entities[entity_type].update(entity_dict)


class BaseEntityManagerSerializer(ABC):
    @abstractmethod
    def dump(self, data: Dict[str, Dict[str, BaseEntity]] | Dict[str, BaseEntity]) -> Any:
        pass

    @abstractmethod
    def load(self, data: Any) -> Dict[str, Dict[str, BaseEntity]] | Dict[str, BaseEntity]:
        pass


class PickleEntityManagerSerializer(BaseEntityManagerSerializer):
    import pickle

    def dump(self, data: Dict[str, Dict[str, BaseEntity]] | Dict[str, BaseEntity]) -> bytes:
        return self.pickle.dumps(data)

    def load(self, data: Any) -> Dict[str, Dict[str, BaseEntity]] | Dict[str, BaseEntity]:
        return self.pickle.loads(data)
