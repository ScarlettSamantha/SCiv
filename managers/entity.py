from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from data.tiles.base_tile import BaseTile
from mixins.singleton import Singleton
from enum import Enum
from uuid import uuid4

from gameplay.units.classes._base import UnitBaseClass
from gameplay.improvements import Improvement
from gameplay.city import City
from gameplay.player import Player
from system.entity import BaseEntity
from weakref import ReferenceType, ref
from system.save_file import BaseSaver, SavePickleFile
from main import Openciv


class EntityType(Enum):
    TILE = ("_tiles_", BaseTile)
    UNIT = ("_units_", UnitBaseClass)
    IMPROVEMENT = ("_improvements_", Improvement)
    CITY = ("_cities_", City)
    PLAYER = ("_players_", Player)

    def __init__(self, storage_key: str, base_type: Type[BaseEntity]):
        self.storage_key = storage_key
        self.base_type = base_type


K = TypeVar("K", bound=str)
V = TypeVar("V", bound=BaseEntity)


class BaseEntityManagerSerializer(ABC):
    @abstractmethod
    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity]]) -> Any:
        pass

    @abstractmethod
    def load(self, data: Any) -> Dict[EntityType, Dict[str, BaseEntity]]:
        pass


class PickleEntityManagerSerializer(BaseEntityManagerSerializer):
    import pickle

    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity]]) -> bytes:
        return self.pickle.dumps(data)

    def load(self, data: Any) -> Dict[EntityType, Dict[str, BaseEntity]]:
        return self.pickle.loads(data)


class EntityManager(Singleton):
    _entities: Dict[EntityType, Dict[str, BaseEntity]] = {type_: {} for type_ in EntityType}
    _meta_data: Dict[str, Dict[str, Any]] = {"system": {}, "game": {}, "stats": {}, "player": {}}

    # Default we pick the PickleEntityManagerSerializer
    _default_serializer: Type[BaseEntityManagerSerializer] = PickleEntityManagerSerializer
    _default_savefile_handler: Type[BaseSaver] = SavePickleFile

    def __setup__(
        self,
        base: "Openciv",
        serializer: Optional[Type["BaseEntityManagerSerializer"]] = None,
        saver: Optional[Type["BaseSaver"]] = None,
        session_name: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.base: "Openciv" = base
        self.serializer: BaseEntityManagerSerializer = (
            serializer() if serializer is not None else self._default_serializer()
        )
        self.saver: Type[BaseSaver] = saver if saver is not None else self._default_savefile_handler
        self.session: Optional[str] = session_name if session_name is not None else str(uuid4().hex)
        self.session_incrementer: int = 0  # Used to keep track of how many times the session has been loaded

        # Stats
        self.stats = {
            # Amount of times register is called
            "total_entities_registered": 0,
            # Amount of times unregister is called
            "total_entities_unregistered": 0,
            # Amount of entities registered
            "total_entities": 0,
            # Amount of entities registered but not unregistered.
            "total_orphan_entities": 0,
        }

        return super().__setup__(*args, **kwargs)

    def add_default_meta_data(self) -> None:
        """
        Call this as late to saving as possible so the most accurate stats gets saved.
        """
        self.add_meta_data("stats", self.stats)
        self._meta_data["stats"]["total_orphan_entities"] = (
            self.stats["total_entities_unregistered"] - self.stats["total_entities"]
        )

    def check_object_against_type(self, type: EntityType, entity: object) -> bool:
        return isinstance(entity, type.base_type)

    def object_type_to_storage(self, type: EntityType) -> Dict[str, BaseEntity]:
        return self._entities[type]

    def register(self, type: EntityType, entity: BaseEntity, key: str = str(uuid4().hex), inject_key: bool = True):
        if not self.check_object_against_type(type, entity):
            raise TypeError(f"Entity does not match expected type {type.base_type}")

        self.stats["total_entities_registered"] += 1
        self.stats["total_entities"] += 1

        storage = self.object_type_to_storage(type)
        if key in storage:
            raise ValueError(f"Entity with key {key} already exists.")

        if inject_key:
            entity.entity_key = key
        storage[key] = entity

    def unregister(self, type: EntityType, key: str):
        self.stats["total_entities_unregistered"] += 1
        self.stats["total_entities"] -= 1
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

    def add_meta_data(self, key: str, value: Any):
        self._meta_data[key] = value

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

    def dump(self):
        if not self.serializer:
            raise ValueError("No serializer registered.")

        data = self.serializer.dump(self._entities)

        if self.saver is None:
            raise ValueError("No saver registered.")

        if self.session is None:
            raise ValueError("No session name set.")

        saver_instance = self.saver()
        saver_instance.set_data(data)
        saver_instance.set_identifier(self.session)
        saver_instance.set_incrementer(self.session_incrementer)

        # Add meta data before saving to the file to keep track of the state of the game, keep these as late as possible
        self.add_default_meta_data()
        saver_instance.set_meta_data(self._meta_data)

        saver_instance.save()

    def load(self):
        if self.saver is None:
            raise ValueError("No saver registered.")

        if self.session is None:
            raise ValueError("No session name set.")

        self.clear()

        saver_instance = self.saver()
        saver_instance.set_identifier(self.session)
        loaded_data: str = saver_instance.load()

        self.session_incrementer = saver_instance.get_incrementer()
        self._meta_data = saver_instance.get_saved_meta_data()

        unserialized_data: Dict[EntityType, Dict[str, BaseEntity]] = self.serializer.load(loaded_data)

        for entity_type, entity_dict in unserialized_data.items():
            self._entities[entity_type].update(entity_dict)

    def get_all_session(self):
        if self.saver is None:
            raise ValueError("No saver registered.")

        if self.session is None:
            raise ValueError("No session name set.")

        saver_instance = self.saver()
        return saver_instance.get_saved_session()
