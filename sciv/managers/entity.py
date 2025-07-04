import gc
import importlib
import json
import os
import subprocess  # nosec B404
import uuid
import weakref
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from inspect import isclass
from logging import Logger
from pickletools import genops
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from uuid import uuid4
from weakref import ReferenceType, ref

import orjson
from graphviz import Digraph
from mixins.singleton import Singleton
from mypy.types import JsonDict
from system.entity import BaseEntity
from system.save_file import BaseSaver, SaveJsonFile

from helpers.debug import Debug

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.effect import Effect
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from system.game_settings import GameSettings
    from system.mesh import HexGrid

    from sciv.game import OpenCiv


class EntityType(Enum):
    TILE = ("_tiles_", None)
    UNIT = ("_units_", None)
    IMPROVEMENT = ("_improvements_", None)
    CITY = ("_cities_", None)
    PLAYER = ("_players_", None)
    EFFECT = ("_effects_", None)
    WORLD = ("_world_", None)
    GAME_SETTINGS = ("_game_settings_", None)

    def __init__(
        self,
        storage_key: str,
        base_type: "Type[BaseEntity] | Type[HexGrid] | Type[GameSettings] | None" = None,
    ):
        self.storage_key: str = storage_key
        self._base_type: "Type[BaseEntity] | Type[HexGrid] | Type[GameSettings] | None" = base_type

    @property
    def base_type(
        self,
    ) -> "Type[BaseEntity] | Type[HexGrid] | Type[GameSettings]":
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

DumpFn = Callable[[Any], Any]
LoadFn = Callable[[Any], Any]

HandlerTuple = tuple[DumpFn, LoadFn]
EntityRegistry = Dict[EntityType, Dict[str, BaseEntity | Dict[str, Any]]]
ObjectData = Dict[str, Any]


class BaseEntityManagerSerializer(ABC):
    @abstractmethod
    def dump(self, registry: EntityRegistry) -> bytes:
        pass

    @abstractmethod
    def load(self, data: Any) -> EntityRegistry:
        pass


class JSONEntityManagerSerializer(BaseEntityManagerSerializer):
    def __init__(self) -> None:
        self._handlers: Dict[Type[Any], HandlerTuple] = {}
        self._object_store: Dict[str, ObjectData] = {}
        self._external_objects: Dict[str, Any] = {}
        self._cycle_map: Dict[int, str] = {}

        self.register_handler(
            typ=datetime, dump_fn=lambda dt: dt.isoformat(), load_fn=lambda s: datetime.fromisoformat(s)
        )

    def register_handler(self, typ: Type[Any], dump_fn: DumpFn, load_fn: LoadFn) -> None:
        self._handlers[typ] = (dump_fn, load_fn)

    def _find_bad_json_keys(self, obj: Any, path: Optional[List[Any]] = None) -> List[Tuple[List[Any], Any]]:
        if path is None:
            path = []
        errors: List[Tuple[List[Any], Any]] = []
        if isinstance(obj, dict):
            for key, value in obj.items():  # type:ignore
                if not isinstance(key, (str, int, float, bool, type(None))):
                    errors.append((path + [key], key))  # type:ignore
                errors.extend(self._find_bad_json_keys(value, path + [key]))
        elif isinstance(obj, (list, tuple, set)):
            for idx, item in enumerate(obj):  # type:ignore
                errors.extend(self._find_bad_json_keys(item, path + [idx]))
        return errors

    def _find_bad_json_values(self, obj: Any, path: Optional[List[Any]] = None) -> List[Tuple[List[Any], Any]]:
        if path is None:
            path = []
        errors: List[Tuple[List[Any], Any]] = []
        if isinstance(obj, dict):
            for key, value in obj.items():  # type:ignore
                errors.extend(self._find_bad_json_values(value, path + [key]))
        elif isinstance(obj, (list, tuple, set)):
            for idx, item in enumerate(obj):  # type:ignore
                errors.extend(self._find_bad_json_values(item, path + [idx]))
        else:
            if not isinstance(obj, (str, int, float, bool, type(None))):
                errors.append((path, obj))
        return errors

    def dump(self, registry: EntityRegistry, graph_out: Optional[str] = None) -> bytes:
        from system.game_settings import GameSettings
        from system.mesh import HexGrid

        self._object_store.clear()
        payload: Dict[str, Any] = {}

        for entity_type, entities in registry.items():
            section = entity_type.storage_key.strip("_")
            payload[section] = {}
            for tag, entity in entities.items():
                if not hasattr(entity, "__getstate__") and not hasattr(entity, "__dict__"):
                    raise TypeError(f"Entity {entity} does not have __getstate__ or __dict__ method.")
                if isinstance(entity, BaseEntity):
                    state = entity.__getstate__() if hasattr(entity, "__getstate__") else entity.__dict__.copy()
                elif isinstance(entity, (HexGrid, GameSettings)):
                    state = entity.__dict__.copy()
                elif isinstance(entity, dict):  # type:ignore It always a dict but mypy does not know it
                    state = entity.copy()
                else:
                    raise TypeError(f"Unsupported entity type {type(entity)} for serialization.")
                state = self._apply_handlers(state)
                state = self._extract_external(state)
                state = self._convert_references(state, path=[f"{entity_type.storage_key}.{tag}"])
                state["_cls"] = f"{entity.__class__.__module__}.{entity.__class__.__name__}"
                payload[section][tag] = state

        payload["_objects"] = self._object_store
        if Debug.system_saving():
            bad_keys: List[Tuple[List[Any], Any]] = self._find_bad_json_keys(payload)
            if bad_keys:
                messages: List[str] = []
                for path, key in bad_keys:
                    messages.append(f"Invalid key at {'->'.join(map(str, path))!r}: {key!r} (type {type(key)})")
                raise TypeError("Save aborted: non-serializable dict keys detected:\n" + "\n".join(messages))

            bad_values: List[Tuple[List[Any], Any]] = self._find_bad_json_values(payload)
            if bad_values:
                messages: List[str] = []
                for path, val in bad_values:
                    messages.append(f"Invalid value at {'->'.join(map(str, path))!r}: {val!r} (type {type(val)})")
                raise TypeError("Save aborted: non-serializable dict values detected:\n" + "\n".join(messages))

        return orjson.dumps(payload, option=orjson.OPT_NON_STR_KEYS)

    def load(self, data: Union[bytes, str], graph_out: Optional[str] = None) -> EntityRegistry:
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        parsed = json.loads(text)

        objects_data = parsed.pop("_objects", {})
        cycles_meta = objects_data.pop("_cycles", {})

        self._reconstitute_external(objects=objects_data)

        def _inject_cycles(state: Any) -> Any:
            if isinstance(state, dict):
                if "__cycle_ref__" in state:
                    placeholder = state["__cycle_ref__"]  # type: ignore
                    entry = cycles_meta.get(placeholder)
                    if entry is None:
                        raise ValueError(f"Unknown cycle placeholder '{placeholder}'")
                    return _inject_cycles(entry["state"])
                return {k: _inject_cycles(v) for k, v in state.items()}  # type: ignore
            elif isinstance(state, list):
                return [_inject_cycles(v) for v in state]  # type: ignore
            else:
                return state

        for section in list(parsed.keys()):
            for tag, raw_state in parsed[section].items():
                parsed[section][tag] = _inject_cycles(raw_state)

        registry: EntityRegistry = {etype: {} for etype in EntityType}
        for entity_type in EntityType:
            section = entity_type.storage_key.strip("_")
            for tag, state in parsed.get(section, {}).items():
                cls: "Type[BaseEntity] | Type[HexGrid] | Type[GameSettings]" = entity_type.base_type
                cls_path = state.pop("_cls", None)
                if cls_path:
                    module, name = cls_path.rsplit(".", 1)
                    cls = getattr(__import__(module, fromlist=[name]), name)

                state: Dict[str, Any] = self._restore_handlers({k: v for k, v in state.items() if k != "_cls"})

                entity: BaseEntity = cls.__new__(cls)  # type: ignore
                entity.__dict__.update(state)
                registry[entity_type][tag] = entity

        for entities in registry.values():
            for ent in entities.values():
                self._resolve_references(ent, registry)  # type: ignore

        return registry

    def _apply_handlers(self, state: Any) -> Any:
        if isinstance(state, dict):
            return {k: self._apply_handlers(v) for k, v in state.items()}  # type: ignore
        if isinstance(state, list):
            return [self._apply_handlers(v) for v in state]  # type: ignore
        for typ, (dump_fn, _) in self._handlers.items():
            if isinstance(state, typ):
                return {"__type__": typ.__name__, "value": dump_fn(state)}
        return state

    def _restore_handlers(self, state: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in state.items():
            if isinstance(value, dict) and "__type__" in value:
                typ_name = value["__type__"]  # type: ignore
                for typ, (_, load_fn) in self._handlers.items():
                    if typ.__name__ == typ_name:
                        result[key] = load_fn(value["value"])  # type: ignore
                        break
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def _extract_external(self, state: Any) -> Any:
        if isinstance(state, dict):
            # check for the “external” marker
            if state.get("__is_object__"):  # type: ignore
                obj_key = state.get("entity_key") or uuid.uuid4().hex  # type: ignore
                self._object_store[obj_key] = {
                    "__object__": state["__object__"],
                    "state": state.get("state", {}),  # type: ignore
                }
                return {"__objref__": obj_key}  # type: ignore
            # otherwise recurse
            return {k: self._extract_external(v) for k, v in state.items()}  # type: ignore
        if isinstance(state, list):
            return [self._extract_external(v) for v in state]  # type: ignore
        return state

    def _reconstitute_external(self, objects: Dict[str, ObjectData]) -> None:
        self._external_objects.clear()
        for obj_key, info in objects.items():
            module_name, class_name = info["__object__"].rsplit(".", 1)
            cls = getattr(importlib.import_module(module_name), class_name)
            state = info.get("state", {})
            obj = cls.from_dict(state) if hasattr(cls, "from_dict") else cls(**state)
            self._external_objects[obj_key] = obj

    def _convert_references(
        self, _state: Dict[str, Any], _visited: Optional[Set[int]] = None, path: Optional[List[str]] = None
    ) -> Any:
        if path is None:
            path = []
        if _visited is None:
            _visited = set()
        obj_id = id(_state)

        if isinstance(_state, BaseEntity):
            return {
                "__ref__": _state.entity_key,
                "__class__": _state.__class__.__name__,
                "__module__": _state.__class__.__module__,
            }

        if isinstance(_state, weakref.ReferenceType) and (obj := _state()) is not None:  # type: ignore
            if isinstance(obj, BaseEntity):
                return {
                    "__ref__": obj.entity_key,
                    "__class__": obj.__class__.__name__,
                    "__module__": obj.__class__.__module__,
                }
            state: Any = obj  # type: ignore
        else:
            state: Any = _state  # type: ignore

        if isinstance(state, (int, float, str, bool, type(None), tuple, MappingProxyType)):
            return state  # type: ignore

        if isinstance(state, (set, frozenset)):
            return list(state)  # type: ignore

        if obj_id in _visited:
            placeholder = self._cycle_map.get(obj_id)
            if placeholder is None:
                placeholder = uuid.uuid4().hex
                self._cycle_map[obj_id] = placeholder
                self._object_store.setdefault("_cycles", {})[placeholder] = {"breadcrumb": "->".join(path)}
            return {"__cycle_ref__": placeholder}
        _visited.add(obj_id)

        if isinstance(state, dict) and any(k in state for k in ("__ref__", "__objref__", "__cycle_ref__")):
            return state  # type: ignore

        if isinstance(state, dict):
            return {k: self._convert_references(v, _visited, path + [k]) for k, v in state.items()}  # type: ignore
        if isinstance(state, list):
            return [self._convert_references(v, _visited, path + [f"[{i}]"]) for i, v in enumerate(state)]  #    type: ignore
        if hasattr(state, "__getstate__"):  # type: ignore
            if isclass(state):  # type: ignore
                return {
                    "__class__": state.__name__,
                    "__module__": state.__module__,
                    "__getstate__": "type",
                }
            else:
                st: Dict[str, Dict[str, Any]] = cast(Dict[str, JsonDict], state.__getstate__())  # type: ignore
            if isinstance(st, dict):  # type: ignore
                return self._convert_references(st, _visited, path + [state.__class__.__name__ + ".__getstate__()"])  # type: ignore
        if hasattr(state, "__dict__"):  # type: ignore
            _state_dict: Dict[str, Any] = cast(Dict[str, Any], state.__dict__)  # type: ignore
            return self._convert_references(_state_dict, _visited, path + [state.__class__.__name__])  # type: ignore
        if hasattr(state, "to_dict"):  # type: ignore
            try:
                return self._convert_references(
                    state.to_dict(),  # type: ignore
                    _visited,
                    path + [state.__class__.__name__ + ".to_dict()"],  # type: ignore
                )
            except Exception:
                pass

        breadcrumb = "->".join(path) or "<root>"
        raise ValueError(f"Unsupported type for conversion to references at '{breadcrumb}': {type(state)}")  # type: ignore

    def _resolve_references(self, entity: BaseEntity, registry: EntityRegistry) -> None:
        for attr, val in list(entity.__dict__.items()):
            if isinstance(val, dict) and "__ref__" in val:
                ref_key: str = cast(str, val["__ref__"])
                for table in registry.values():
                    if ref_key in table:
                        setattr(entity, attr, weakref.ref(table[ref_key]))
                        break
            elif isinstance(val, dict) and "__objref__" in val:
                setattr(entity, attr, self._external_objects.get(val["__objref__"]))  # type: ignore
            elif isinstance(val, list):
                converted_list: List[Any] = []
                for item in val:  # type: ignore
                    if isinstance(item, dict) and "__ref__" in item:
                        for table in registry.values():
                            if item["__ref__"] in table:
                                converted_list.append(table[item["__ref__"]])
                                break
                    elif isinstance(item, dict) and "__objref__" in item:
                        converted_list.append(self._external_objects.get(cast(str, item["__objref__"])))
                    else:
                        converted_list.append(item)
                setattr(entity, attr, converted_list)


class EntityManager(Singleton):
    _entities: Dict[EntityType, Dict[str, "BaseEntity | HexGrid | GameSettings"]] = {type_: {} for type_ in EntityType}
    _meta_data: Dict[str, Dict[str, Any]] = {"system": {}, "game": {}, "stats": {}, "player": {}}

    _default_serializer: Type[BaseEntityManagerSerializer] = JSONEntityManagerSerializer
    _default_savefile_handler: Type[BaseSaver] = SaveJsonFile

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
        self.stats: Dict[str, int] = {
            "total_entities_registered": 0,
            "total_entities_unregistered": 0,
            "total_entities": 0,
            "total_orphan_entities": 0,
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

        self.logger.info(f"Dumping entity manager data to session '{session_name}'")

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
            before_time = datetime.now()
            data: bytes = self.serializer.dump(_entity_states)
            self.logger.info(
                f"Entity serialization took {round((datetime.now() - before_time).total_seconds(), 2)} seconds for {len(_entity_states)} entities."
            )

        saver_instance = self.saver()
        saver_instance.set_data(data)
        saver_instance.loaded_data_length = len(data)
        saver_instance.set_identifier(self.session)
        saver_instance.set_session_incrementor(self.session_incrementor)

        # Add meta data before saving to the file to keep track of the state of the game, keep these as late as possible
        self.add_default_meta_data()
        self.add_meta_data("loaded_data_length", saver_instance.loaded_data_length)
        saver_instance.set_meta_data(self._meta_data)

        before_save_time = datetime.now()
        saver_instance.save(self.logger.getChild("saver"))
        self.logger.info(
            f"Entity manager data saved to session '{session_name}' in {round((datetime.now() - before_save_time).total_seconds(), 2)} seconds."
        )

    def load(self):
        from system.game_settings import GameSettings
        from system.mesh import HexGrid

        if not self.session:
            raise ValueError("No session name set.")

        saver = self.saver()
        saver.set_identifier(self.session)
        raw_data = saver.load(self.logger.getChild("loader"))

        self.session_incrementor = saver.get_session_incrementor()
        self._meta_data = saver.get_saved_meta_data()

        states: EntityRegistry = self.serializer.load(
            raw_data,
        )

        new_entities: Dict[EntityType, Dict[str, BaseEntity | GameSettings | HexGrid]] = {
            etype: {} for etype in EntityType
        }

        for entity_type, entries in states.items():
            for state in entries.values():
                instance = self._create_instance(entity_type, state)  # type: ignore

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
            cls: "Type[Tile] | Type[Unit] | Type[Improvement] | Type[City] | Type[Player] | Type[Effect] | Type[BaseEntity] | Type[HexGrid] | Type[GameSettings]" = entity_type.base_type

        instance: Tile | Unit | Improvement | City | Player | Effect | BaseEntity | HexGrid | GameSettings = (
            cls.__new__(cls)
        )
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
