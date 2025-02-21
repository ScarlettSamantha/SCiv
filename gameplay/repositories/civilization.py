from random import choice
from system.pyload import PyLoad
from gameplay.civilization import Civilization as BaseCivilization
from typing import Dict, List, Type


class Civilization:
    raw_cache: List[Type[BaseCivilization]] = []
    cache: Dict[str, Type[BaseCivilization]] = {}

    @classmethod
    def all(cls) -> List[Type[BaseCivilization]]:
        if cls.raw_cache.__len__() > 0:
            return cls.raw_cache

        classes = PyLoad.load_classes(
            "gameplay/civilizations", base_classes=BaseCivilization
        )
        for key, _class in classes.items():
            # Remove the base class from the list.
            if _class == BaseCivilization:
                del classes[key]
            cls.raw_cache.append(_class)
            cls.cache[str(_class.name).lower()] = _class

        return list(classes.values())

    @classmethod
    def random(
        cls, num: int = 1, unique: bool = False
    ) -> Type[BaseCivilization] | List[Type[BaseCivilization]]:
        _selected_civilizations: List[Type[BaseCivilization]] = []

        for _ in range(num):
            while True:
                _selected_civilization: Type[BaseCivilization] = choice(cls.all())

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
            cls.all()
        if key not in list(cls.cache.keys()):
            raise ValueError(f"Key {key} not found in cache")
        return cls.cache[key]

    @classmethod
    def get(cls, key: str) -> Type[BaseCivilization]:  # just a wrapper for search
        return cls.search(key)
