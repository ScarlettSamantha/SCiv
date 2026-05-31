import inspect
from random import choice
from typing import Dict, List, Type

from system.generators.base import BaseGenerator
from system.pyload import PyLoad


class GeneratorRepository:
    raw_cache: List[Type[BaseGenerator]] = []
    cache: Dict[str, Type[BaseGenerator]] = {}

    @classmethod
    def all(cls) -> List[Type[BaseGenerator]]:
        if cls.raw_cache:
            return cls.raw_cache

        classes = PyLoad.load_classes("system/generators", base_classes=BaseGenerator)
        generators: List[Type[BaseGenerator]] = []

        for _class in classes.values():
            if _class == BaseGenerator or _class.__name__ == "BaseGenerator":
                continue
            if not inspect.isclass(_class):
                continue
            if not issubclass(_class, BaseGenerator):
                continue
            if inspect.isabstract(_class):
                continue
            if _class.__module__ in {
                "system.generators.base",
                "system.generators.resource_allocator",
            }:
                continue
            generators.append(_class)

        generators.sort(key=lambda generator: str(getattr(generator, "NAME", generator.__name__)).lower())
        cls.raw_cache = generators
        cls.cache = {str(getattr(generator, "NAME", generator.__name__)).lower(): generator for generator in generators}
        return cls.raw_cache

    @classmethod
    def get(cls, key: str) -> Type[BaseGenerator]:
        lookup = key.lower()
        if not cls.cache:
            cls.all()
        if lookup not in cls.cache:
            raise ValueError(f"Generator '{key}' not found")
        return cls.cache[lookup]

    @classmethod
    def cache_refresh(cls) -> None:
        cls.raw_cache = []
        cls.cache = {}

    @classmethod
    def random(cls, num: int = 1, unique: bool = False) -> Type[BaseGenerator] | List[Type[BaseGenerator]]:
        _selected_generators: List[Type[BaseGenerator]] = []

        for _ in range(num):
            while True:
                _selected_personality: Type[BaseGenerator] = choice(cls.all())

                if unique and _selected_personality in _selected_generators:
                    continue

                _selected_generators.append(_selected_personality)
                break

            if num == 1:
                return _selected_personality

        return _selected_generators
