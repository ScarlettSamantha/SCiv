from typing import Dict, Type

from gameplay.units.unit_base import UnitBaseClass
from system.pyload import PyLoad


class UnitRepository:
    _cache: Dict[str, Type[UnitBaseClass]] = {}

    @classmethod
    def all(cls, use_cache: bool = True) -> Dict[str, Type[UnitBaseClass]]:
        if use_cache and len(cls._cache) > 0:
            return cls._cache

        classes: Dict[str, Type[UnitBaseClass]] = PyLoad.load_classes("gameplay/units/core", base_classes=UnitBaseClass)
        filtered: Dict[str, Type[UnitBaseClass]] = {}
        for key, _class in classes.items():
            if issubclass(_class, UnitBaseClass):
                filtered[key] = _class

        if use_cache:
            cls._cache = filtered

        return filtered

    @classmethod
    def get(cls, key: str, use_cache: bool = True) -> Type[UnitBaseClass]:
        return cls.all(use_cache=use_cache)[key]

    @classmethod
    def has(cls, key: str, use_cache: bool = True) -> bool:
        return key in cls.all(use_cache=use_cache)

    @classmethod
    def get_all_buildable_units(cls, use_cache: bool = True) -> Dict[str, Type[UnitBaseClass]]:
        return {_: unit for _, unit in cls.all(use_cache=use_cache).items() if unit.buildable}
