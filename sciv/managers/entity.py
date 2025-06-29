from abc import ABC, abstractmethod
from enum import Enum
import gc
from logging import Logger
import os
from pickletools import genops
import subprocess  # nosec B404
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
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from sciv.game import OpenCiv
    from gameplay.effect import Effect
    from system.mesh import HexGrid
    from system.game_settings import GameSettings


class EntityType(Enum):
    TILE = ("_tiles_", None)
    UNIT = ("_units_", None)
    IMPROVEMENT = ("_improvements_", None)
    CITY = ("_cities_", None)
    PLAYER = ("_players_", None)
    EFFECT = ("_effects_", None)
    WORLD = ("_world_", None)
    GAME_SETTINGS = ("_game_settings_", None)

    def __init__(self, storage_key: str, base_type: Type["BaseEntity"] | None):
        self.storage_key = storage_key
        self._base_type = base_type  # Store it privately

    @property
    def base_type(
        self,
    ) -> "type[Tile] | type[Unit] | type[Improvement] | type[City] | type[Player] | type[Effect] | Type[BaseEntity] | Type[HexGrid] | Type[GameSettings]":
        """Lazy import to avoid circular dependencies."""
        if self._base_type is None:
            if self == EntityType.TILE:
                from gameplay.tile import Tile

                self._base_type = Tile
            elif self == EntityType.UNIT:
                from gameplay.unit import Unit

                self._base_type = Unit
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
                from gameplay.effect import Effect

                self._base_type = Effect
            elif self == EntityType.WORLD:
                from system.mesh import HexGrid

                self._base_type = HexGrid
            elif self == EntityType.GAME_SETTINGS:
                from system.game_settings import GameSettings

                self._base_type = GameSettings
            else:
                raise NotImplementedError(f"Entity type {self} not implemented.")

        return self._base_type


K = TypeVar("K", bound=str)
V = TypeVar("V", bound="BaseEntity")


class BaseEntityManagerSerializer(ABC):
    @abstractmethod
    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity | Dict[str, Any]]]) -> bytes:
        pass

    @abstractmethod
    def load(self, data: Any) -> Dict[EntityType, Dict[str, Dict[str, Any]]]:
        pass


class PickleEntityManagerSerializer(BaseEntityManagerSerializer):
    def dump(self, data: Dict[EntityType, Dict[str, BaseEntity | Dict[str, Any]]]) -> bytes:
        from helpers.debug import Debug
        import dill as pickle  # type: ignore

        if Debug.system_saving():
            import dill.detect

            with dill.detect.trace():  # Enable tracing for debugging purposes # type: ignore
                return dill.dumps(data, recurse=False, byref=False)  # type: ignore
        return pickle.dumps(data, recurse=True, byref=True)  # type: ignore

    def load(self, data: Any) -> Dict[EntityType, Dict[str, Dict[str, Any]]]:
        from helpers.debug import Debug
        import dill as pickle  # type: ignore

        if Debug.system_loading():
            import dill.detect

            with dill.detect.trace():  # type: ignore
                return pickle.loads(data)  # type: ignore

        return pickle.loads(data, ignore=True)  # type: ignore


class EntityManager(Singleton):
    _entities: Dict[EntityType, Dict[str, "BaseEntity | HexGrid | GameSettings"]] = {type_: {} for type_ in EntityType}
    _meta_data: Dict[str, Dict[str, Any]] = {"system": {}, "game": {}, "stats": {}, "player": {}}

    # Default we pick the PickleEntityManagerSerializer
    _default_serializer: Type[BaseEntityManagerSerializer] = PickleEntityManagerSerializer
    _default_savefile_handler: Type[BaseSaver] = SavePickleFile

    def __setup__(
        self,
        base: "OpenCiv",
        serializer: Optional[Type["BaseEntityManagerSerializer"]] = None,
        saver: Optional[Type["BaseSaver"]] = None,
        session_name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.base: "OpenCiv" = base
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
            "voxels": 0,
            "faces": 0,
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
        self._entities: Dict[EntityType, Dict[str, "BaseEntity | HexGrid | GameSettings"]] = {
            type_: {} for type_ in EntityType
        }

    def add_default_meta_data(self) -> None:
        self.add_meta_data("stats", self.stats)
        self._meta_data["stats"]["total_orphan_entities"] = (
            self.stats["total_entities_unregistered"] - self.stats["total_entities"]
        )
        self._meta_data["game"]["version"] = self.base.version
        self._meta_data["game"]["commit"] = self.base.commit

    def check_object_against_type(self, type: EntityType, entity: object) -> bool:
        return isinstance(entity, type.base_type)

    def __getstate__(self) -> Dict[Any, Any]:
        return {}

    def calculate_stats(self):
        self.stats["total_players"] = len(self._entities[EntityType.PLAYER])
        self.stats["total_units"] = len(self._entities[EntityType.UNIT])
        self.stats["total_tiles"] = len(self._entities[EntityType.TILE])
        self.stats["total_effects"] = len(self._entities[EntityType.EFFECT])

    def object_type_to_storage(self, type: EntityType) -> Dict[str, "BaseEntity | HexGrid | GameSettings"]:
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
        key = entity.tag if hasattr(entity, "tag") else entity.entity_key

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
    ) -> "BaseEntity | ReferenceType[BaseEntity | HexGrid | GameSettings] | HexGrid | GameSettings | None":
        storage = self.object_type_to_storage(type)
        entity = storage.get(key)
        return ref(entity) if weak_ref and entity else entity

    def get_ref_weak(self, type: EntityType, key: str) -> ReferenceType["BaseEntity | HexGrid | GameSettings"]:
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
    ) -> list["BaseEntity | ReferenceType[BaseEntity | HexGrid | GameSettings] | GameSettings | HexGrid | None"]:
        return [self.get_ref(type, key, weak_ref=weak_refs) for key in keys]

    def add_meta_data(self, key: str, value: Any):
        self._meta_data[key] = value

    def get_meta_data(self, key: str) -> Any:
        return self._meta_data[key]

    def get_all_improvements(self) -> Dict[str, "Improvement"]:
        return self.get_all(type=EntityType.IMPROVEMENT)  # type: ignore # its fine it does not know that the base entity can only be an Improvement

    def get_all_units(self) -> Dict[str, "Unit"]:
        return self.get_all(type=EntityType.UNIT)  # type: ignore # its fine it does not know that the base entity can only be a Unit

    def get_all_tiles(self) -> Dict[str, "Tile"]:
        return self.get_all(type=EntityType.TILE)  # type: ignore # its fine it does not know that the base entity can only be a Tile

    def get_all_cities(self) -> Dict[str, "City"]:
        return self.get_all(type=EntityType.CITY)  # type: ignore # its fine it does not know that the base entity can only be a City

    def get_all_players(self) -> Dict[str, "Player"]:
        return self.get_all(type=EntityType.PLAYER)  # type: ignore # its fine it does not know that the base entity can only be a Player

    def get_all(self, type: Optional[EntityType] = None) -> Dict[str, "BaseEntity | HexGrid | GameSettings"]:
        if type is None:
            return {key: entity for storage in self._entities.values() for key, entity in storage.items()}
        return self.object_type_to_storage(type)

    def get_all_refs(self, type: EntityType) -> Dict[str, ReferenceType["BaseEntity | HexGrid | GameSettings"]]:
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

    def dump(self, session_name: str = ""):
        from helpers.debug import Debug

        if not self.serializer:
            raise ValueError("No serializer registered.")

        if session_name == "" or len(session_name) == 0:
            session_name = self.session if self.session is not None else "default_session"

        self.session = session_name

        if Debug.system_entity_graph() is True:
            data: bytes = self.debug_dump(keep_profile=True)
        else:
            _entity_states: Dict[EntityType, Dict[str, Any]] = {
                etype: {key: entity.__getstate__() for key, entity in entities.items()}
                for etype, entities in self._entities.items()
            }
            data: bytes = self.serializer.dump(_entity_states)

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
        from system.mesh import HexGrid
        from system.game_settings import GameSettings

        if not self.session:
            raise ValueError("No session name set.")

        saver = self.saver()
        saver.set_identifier(self.session)
        raw_data = saver.load()

        self.session_incrementor = saver.get_session_incrementor()
        self._meta_data = saver.get_saved_meta_data()

        states: Dict[EntityType, Dict[str, Dict[str, Any]]] = self.serializer.load(
            raw_data,
        )

        new_entities: Dict[EntityType, Dict[str, BaseEntity | GameSettings | HexGrid]] = {
            etype: {} for etype in EntityType
        }

        for entity_type, entries in states.items():
            for state in entries.values():
                instance = self._create_instance(entity_type, state)

                if isinstance(instance, BaseEntity):
                    key = getattr(instance, "entity_key", None)
                elif isinstance(instance, GameSettings):
                    key = "game_settings"
                elif isinstance(instance, HexGrid):  # type: ignore
                    key = "world_grid"
                else:
                    raise TypeError(
                        f"Unsupported entity type {type(instance)} for entity_type {entity_type.name}. "
                        "Expected BaseEntity, HexGrid, or GameSettings."
                    )

                if not isinstance(key, str):
                    raise ValueError(f"Entity key must be a string, got {type(key)}")
                # Register loaded instance without altering its state

                assert (
                    isinstance(instance, BaseEntity)
                    or isinstance(instance, HexGrid)
                    or isinstance(instance, GameSettings)
                ), f"Instance must be a BaseEntity or HexGrid, got {type(instance)}"
                assert key is not None, f"Entity key cannot be None for {entity_type.name}."
                new_entities[entity_type][key] = instance
        del states
        self.clear()
        gc.collect()
        self._entities = new_entities

    def _create_instance(self, entity_type: EntityType, state: Dict[str, Any]) -> "BaseEntity | HexGrid | GameSettings":
        if entity_type == EntityType.UNIT:
            class_path = state.get("unit")
            if not class_path:
                raise ValueError("Unit class is not defined in the entity data.")
            module_name, class_name = class_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
        else:
            cls = entity_type.base_type

        instance = cls.__new__(cls)
        instance.__setstate__(state)

        return instance

    def get_all_session(self) -> List[str]:
        if self.session is None:
            raise ValueError("No session name set.")

        saver_instance = self.saver()
        return saver_instance.get_saved_session()

    def get_session_data(self, session_name: str) -> None | Dict[str, Any]:
        saver_instance = self.saver()
        saver_instance.set_identifier(session_name)
        return saver_instance.get_session_data()

    def graph_pickle(
        self,
        data: Dict[EntityType, Dict[str, BaseEntity]],
        out_dot: str | None = None,
        out_png: str | None = None,
    ):
        import dill

        session = self.session or uuid4().hex
        out_dot = out_dot or f"debugging/{session}_object_graph.dot"
        os.makedirs(os.path.dirname(out_dot), exist_ok=True)

        try:
            raw = dill.dumps(data, recurse=True)  # type: ignore
        except Exception as full_exc:
            self.logger.warning(f"[graph_pickle] full dill.dumps failed: {full_exc!r}; falling back to class-only dump")
            class_only = {etype.name: tuple({type(ent) for ent in ents.values()}) for etype, ents in data.items()}
            raw = dill.dumps(class_only)  # type: ignore

        edges: list[tuple[str, str]] = []
        last_global: str | None = None

        for opcode, arg, _ in genops(raw):  #  type: ignore
            if opcode.name == "GLOBAL" and isinstance(arg, str):
                module, name = arg.split()
                node = f"{module}.{name}"

                if last_global:
                    edges.append((last_global, node))
                last_global = node

            elif opcode.name in ("PUT", "BINPUT", "LONG_BINPUT"):
                last_global = None

        from graphviz import Digraph

        dot: Digraph = Digraph(comment="Pickle Object Graph", format="png")
        for src, dst in edges:
            dot.edge(src, dst)  # type: ignore

        dot.render(filename=out_dot, cleanup=False)  # type: ignore

        self.logger.info(f"[graph_pickle] DOT written to {out_dot} (+ .png)")

    def debug_dump(self, keep_profile: bool = False) -> bytes:
        # ensure our debug dir exists
        if not os.path.exists("debugging"):
            os.makedirs("debugging")

        prof_filename = f"debugging/{self.session}_serialization.prof"
        trace_filename = f"debugging/{self.session}_serialization.trace.log"
        png_filename = f"debugging/{self.session}_serialization.call.png"

        try:
            data: bytes = self.serializer.dump(self._entities)  #    type: ignore
        except Exception as e:
            cmd_g2d = ["/usr/bin/python3", "-m", "gprof2dot", "-f", "pstats", prof_filename]
            cmd_dot = ["dot", "-Tpng", "-o", png_filename]
            proc = subprocess.Popen(cmd_g2d, stdout=subprocess.PIPE)  # nosec B603
            subprocess.run(cmd_dot, stdin=proc.stdout, check=True)  # nosec B603
            proc.wait()

            try:
                self.graph_pickle(self._entities)  # type: ignore
            except Exception as e:
                self.logger.warning(f"Failed to graph pickle: {e!r}")

            if not keep_profile:
                try:
                    os.remove(prof_filename)
                except OSError:
                    pass

            self.logger.info(f"Serialization call-graph written to {png_filename}")
            raise RuntimeError(
                f"Serialization failed due to error. See {trace_filename} for the dill-detect trace. There is more logging in the debugging folder."
            )
        return data

    def remove(self, type: EntityType, key: str):
        if not self.has(type, key):
            self.logger.warning(f"Entity {str(key)} does not exist, cannot remove.")
            return

        entity = self.get(type, key)
        if entity is None:
            self.logger.warning(f"Entity {str(key)} is None, cannot remove.")
            return

        del self.object_type_to_storage(type)[key]
        self.unregister(type, entity)
        self.stats["total_orphan_entities"] = self.stats["total_entities_unregistered"] - self.stats["total_entities"]
