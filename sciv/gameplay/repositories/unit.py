from typing import Dict, Type


from gameplay.promotion import Promotion, PromotionTree
from gameplay.unit import Unit
from system.pyload import PyLoad


class UnitRepository:
    _cache: Dict[str, Type[Unit]] = {}

    @classmethod
    def all(cls, use_cache: bool = True) -> Dict[str, Type[Unit]]:
        if use_cache and len(cls._cache) > 0:
            return cls._cache
        classes_civilian: Dict[str, Type[Unit]] = PyLoad.load_classes(
            ["gameplay/units/core/classes/civilian"],
            base_classes=Unit,
            package="gameplay.units.core.classes.civilian",
        )
        classes_military: Dict[str, Type[Unit]] = PyLoad.load_classes(
            ["gameplay/units/core/classes/military"],
            base_classes=Unit,
            package="gameplay.units.core.classes.military",
        )
        filtered: Dict[str, Type[Unit]] = {}
        for key, _class in (classes_civilian | classes_military).items():
            if issubclass(_class, (Promotion, PromotionTree)):
                continue
            filtered[key] = _class

        if use_cache:
            cls._cache = filtered

        return filtered

    @classmethod
    def get(cls, key: str, use_cache: bool = True) -> Type[Unit]:
        return cls.all(use_cache=use_cache)[key]

    @classmethod
    def has(cls, key: str, use_cache: bool = True) -> bool:
        return key in cls.all(use_cache=use_cache)

    @classmethod
    def get_all_buildable_units(cls, use_cache: bool = True) -> Dict[str, Type[Unit]]:
        return {_: unit for _, unit in cls.all(use_cache=use_cache).items() if unit.buildable}
