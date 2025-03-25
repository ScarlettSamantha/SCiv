from abc import ABC, abstractmethod
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar
from uuid import uuid4
from weakref import ReferenceType, ref

from mixins.singleton import Singleton
from system.entity import BaseEntity
from system.save_file import BaseSaver, SavePickleFile

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.units.unit_base import UnitBaseClass
    from main import SCIV
    from system.effects import Effect


class EntityType(Enum):
    TILE = ("_tiles_", None)
    UNIT = ("_units_", None)
    IMPROVEMENT = ("_improvements_", None)
    CITY = ("_cities_", None)
    PLAYER = ("_players_", None)
    EFFECT = ("_effects_", None)

    def __init__(self, storage_key: str, base_type: Type["BaseEntity"] | None):
        self.storage_key = storage_key
        self._base_type = base_type  # Store it privately

    @property
    def base_type(
        self,
    ) -> "type[BaseTile] | type[UnitBaseClass] | type[Improvement] | type[City] | type[Player] | type[Effect] | Type[BaseEntity]":
        """Lazy import to avoid circular dependencies."""
        if self._base_type is None:
            if self == EntityType.TILE:
                from gameplay.tiles.base_tile import BaseTile

                self._base_type = BaseTile
            elif self == EntityType.UNIT:
                from gameplay.units.unit_base import UnitBaseClass

                self._base_type = UnitBaseClass
            elif self == EntityType.IMPROVEMENT:
                from gameplay.improvement import Improvement

                self._base_type = Improvement
            elif self == EntityType.CITY:
                from gameplay.city import City

                self._base_type = City
            elif self == EntityType.PLAYER:
                from gameplay.player import Player

                self._base_type = Player
            elif self == EntityType.EFFECT:
                from system.effects import Effect

                self._base_type = Effect
            else:
                raise NotImplementedError(f"Entity type {self} not implemented.")

        return self._base_type


K = TypeVar("K", bound=str)
V = TypeVar("V", bound="BaseEntity")


class BaseEntityManagerSerializer(ABC):
    @abstractmethod
    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity]]) -> Any:
        pass

    @abstractmethod
    def load(self, data: Any) -> Dict[EntityType, Dict[str, BaseEntity]]:
        pass


class PickleEntityManagerSerializer(BaseEntityManagerSerializer):
    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity]]) -> bytes:
        import dill as pickle
        import dill.detect

        with dill.detect.trace():  # type: ignore
            return pickle.dumps(data)

    def load(self, data: Any) -> Dict[EntityType, Dict[str, BaseEntity]]:
        import dill as pickle

        return pickle.loads(data)


class EntityManager(Singleton):
    _entities: Dict[EntityType, Dict[str, BaseEntity]] = {type_: {} for type_ in EntityType}
    _meta_data: Dict[str, Dict[str, Any]] = {"system": {}, "game": {}, "stats": {}, "player": {}}

    # Default we pick the PickleEntityManagerSerializer
    _default_serializer: Type[BaseEntityManagerSerializer] = PickleEntityManagerSerializer
    _default_savefile_handler: Type[BaseSaver] = SavePickleFile

    def __setup__(
        self,
        base: "SCIV",
        serializer: Optional[Type["BaseEntityManagerSerializer"]] = None,
        saver: Optional[Type["BaseSaver"]] = None,
        session_name: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.base: "SCIV" = base
        self.serializer: BaseEntityManagerSerializer = (
            serializer() if serializer is not None else self._default_serializer()
        )
        self.saver: Type[BaseSaver] = saver if saver is not None else self._default_savefile_handler
        self.session: Optional[str] = session_name if session_name is not None else str(uuid4().hex)
        self.session_incrementor: int = 0  # Used to keep track of how many times the session has been loaded
        self.logger: Logger = self.base.logger.engine.getChild("manager.entity")

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
            # Dynamic stats
            "total_players": 0,
            "total_units": 0,
            "total_tiles": 0,
            "total_effects": 0,
        }

        return super().__setup__(*args, **kwargs)

    def reset(self):
        self._meta_data = {"system": {}, "game": {}, "stats": {}, "player": {}}
        self.stats = {
            "total_entities_registered": 0,
            "total_entities_unregistered": 0,
            "total_entities": 0,
            "total_orphan_entities": 0,
            "total_players": 0,
            "total_units": 0,
            "total_tiles": 0,
            "total_effects": 0,
        }
        self.session = str(uuid4().hex)
        self.session_incrementor = 0
        self._entities = {type_: {} for type_ in EntityType}

    def add_default_meta_data(self) -> None:
        """
        Call this as late to saving as possible so the most accurate stats gets saved.
        """
        self.add_meta_data("stats", self.stats)
        self._meta_data["stats"]["total_orphan_entities"] = (
            self.stats["total_entities_unregistered"] - self.stats["total_entities"]
        )

    def check_object_against_type(self, type: EntityType, entity: object) -> bool:
        if type.base_type is None:
            return False
        return isinstance(entity, type.base_type)

    def __getstate__(self) -> Dict[Any, Any]:
        return {}

    def calculate_stats(self):
        self.stats["total_players"] = len(self._entities[EntityType.PLAYER])
        self.stats["total_units"] = len(self._entities[EntityType.UNIT])
        self.stats["total_tiles"] = len(self._entities[EntityType.TILE])
        self.stats["total_effects"] = len(self._entities[EntityType.EFFECT])

    def object_type_to_storage(self, type: EntityType) -> Dict[str, BaseEntity]:
        return self._entities[type]

    def register(self, type: EntityType, entity: BaseEntity, key: str):
        if not self.check_object_against_type(type, entity):
            raise TypeError(f"Entity does not match expected type {type.base_type}")

        storage = self.object_type_to_storage(type)
        if key in storage:
            return

        self.stats["total_entities_registered"] += 1
        self.stats["total_entities"] += 1

        entity.entity_key = key
        entity.entity_type_ref = type.storage_key
        entity.is_registered = True
        storage[key] = entity

    def unregister(self, type: EntityType, entity: BaseEntity):
        key = entity.entity_key

        if key is None:
            self.logger.warning(f"Entity {str(entity)} has no key, cannot unregister.")
            return  # Already unregistered

        entity.is_registered = False
        entity.entity_key = None
        entity.entity_type_ref = None

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

    def get_ref_weak(self, type: EntityType, key: str) -> ReferenceType[BaseEntity]:
        unit_ref = self.get_ref(type, key, weak_ref=True)

        if not isinstance(unit_ref, ReferenceType):
            raise ValueError(f"Entity with key {key} does not exist.")
        return unit_ref

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

    def get_meta_data(self, key: str) -> Any:
        return self._meta_data[key]

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

    def dump(self, session_name=""):
        if not self.serializer:
            raise ValueError("No serializer registered.")

        if session_name == "" or len(session_name) == 0:
            session_name = self.session

        self.session = session_name

        data: bytes = self.serializer.dump(self._entities)

        if self.saver is None:
            raise ValueError("No saver registered.")

        if self.session is None:
            raise ValueError("No session name set.")

        saver_instance = self.saver()
        saver_instance.set_data(data)
        saver_instance.loaded_data_length = len(data)
        saver_instance.set_identifier(self.session)
        saver_instance.set_session_incrementor(self.session_incrementor)

        # Add meta data before saving to the file to keep track of the state of the game, keep these as late as possible
        self.add_default_meta_data()
        self.add_meta_data("loaded_data_length", saver_instance.loaded_data_length)
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

        self.session_incrementor = saver_instance.get_session_incrementor()
        self._meta_data = saver_instance.get_saved_meta_data()

        unserialized_data: Dict[EntityType, Dict[str, BaseEntity]] = self.serializer.load(loaded_data)

        for entity_type, entity_dict in unserialized_data.items():
            self._entities[entity_type].update(entity_dict)

    def get_all_session(self) -> List[str]:
        if self.saver is None:
            raise ValueError("No saver registered.")

        if self.session is None:
            raise ValueError("No session name set.")

        saver_instance = self.saver()
        return saver_instance.get_saved_session()

    def get_session_data(self, session_name: str) -> None | Dict[str, Any]:
        if self.saver is None:
            raise ValueError("No saver registered.")

        saver_instance = self.saver()
        saver_instance.set_identifier(session_name)
        return saver_instance.get_session_data()
