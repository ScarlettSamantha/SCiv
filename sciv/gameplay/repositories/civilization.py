from random import choice
from typing import Dict, List, Type

from gameplay.civilization import Civilization as BaseCivilization
from system.pyload import PyLoad


class Civilization:
    raw_cache: List[Type[BaseCivilization]] = []
    cache: Dict[str, Type[BaseCivilization]] = {}
    excluded_civilizations: List[str] = ["barbarians", "nature"]

    @classmethod
    def all(cls, enable_exclude: bool = True) -> List[Type[BaseCivilization]]:
        if cls.raw_cache.__len__() > 0:
            if enable_exclude:
                allowed = [c for c in cls.raw_cache if str(c.name).lower() not in cls.excluded_civilizations]
                return allowed
            return cls.raw_cache

        classes = PyLoad.load_classes("gameplay/civilizations", base_classes=BaseCivilization)
        for key, _class in classes.items():
            # Remove the base class from the list.
            if _class == BaseCivilization:
                del classes[key]
            cls.raw_cache.append(_class)
            cls.cache[str(_class.name).lower()] = _class

        return (
            cls.raw_cache
            if not enable_exclude
            else [c for c in cls.raw_cache if str(c.name).lower() not in cls.excluded_civilizations]
        )

    @classmethod
    def random(
        cls, num: int = 1, unique: bool = False, exclude: bool = True
    ) -> Type[BaseCivilization] | List[Type[BaseCivilization]]:
        _selected_civilizations: List[Type[BaseCivilization]] = []

        for _ in range(num):
            while True:
                _selected_civilization: Type[BaseCivilization] = choice(cls.all(enable_exclude=exclude))

                if unique and _selected_civilization in _selected_civilizations:
                    continue

                _selected_civilizations.append(_selected_civilization)
                break

            if num == 1:
                return _selected_civilization

        return _selected_civilizations

    @classmethod
    def cache_refresh(cls) -> None:
        cls.cache = {}
        cls.raw_cache = []
        cls.all()

    @classmethod
    def search(cls, key: str) -> Type[BaseCivilization]:
        key = key.lower()
        if cls.cache.__len__() == 0:
            cls.all(enable_exclude=False)
        if key not in list(cls.cache.keys()):
            raise ValueError(f"Key {key} not found in cache")
        return cls.cache[key]

    @classmethod
    def get(cls, key: str) -> Type[BaseCivilization]:  # just a wrapper for search
        return cls.search(key)
