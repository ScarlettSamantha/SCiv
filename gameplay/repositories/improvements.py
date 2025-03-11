from typing import Dict, Type

from gameplay.improvement import Improvement
from gameplay.improvements.core.city.barracks import BaseCityImprovement
from system.pyload import PyLoad


class ImprovementsRepository:
    _cache: Dict[str, Type[Improvement]] = {}

    @classmethod
    def all(cls, use_cache: bool = True) -> Dict[str, Type[Improvement]]:
        if use_cache and cls._cache:
            return cls._cache

        classes = PyLoad.load_classes("gameplay/improvements", base_classes=Improvement)
        for key, _class in classes.items():
            if _class == Improvement:
                del classes[key]

        if use_cache:
            cls._cache = classes

        return classes

    @classmethod
    def get(cls, name: str, use_cache: bool = True) -> Type[Improvement]:
        if use_cache and cls._cache and name in cls._cache.keys():
            return cls._cache[name]
        return cls.all(use_cache=use_cache)[name]

    @classmethod
    def get_all_by_type(
        cls, parent_improvement_type: type[Improvement], use_cache: bool = True
    ) -> Dict[str, Type[Improvement]]:
        all_improvements: Dict[str, Type[Improvement]] = cls.all(use_cache=use_cache)
        result = {}
        for name, improvement in all_improvements.items():
            if issubclass(improvement, parent_improvement_type) and not improvement == parent_improvement_type:
                result[name] = improvement

        return result

    @classmethod
    def get_all_city_improvements(cls, use_cache: bool = True) -> Dict[str, Type[BaseCityImprovement]]:
        return cls.get_all_by_type(parent_improvement_type=BaseCityImprovement, use_cache=use_cache)  # type: ignore # this is what this method is supposed to do.
