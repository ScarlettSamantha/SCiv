from random import choice
from typing import List, Type
from system.generators.base import BaseGenerator
from system.pyload import PyLoad


class GeneratorRepository:
    @classmethod
    def all(cls) -> List[Type[BaseGenerator]]:
        classes = PyLoad.load_classes(
            "gameplay/personalities", base_classes=BaseGenerator
        )
        for key, _class in classes.items():
            if _class == BaseGenerator:
                del classes[key]
        return list(classes.values())

    @classmethod
    def random(
        cls, num: int = 1, unique: bool = False
    ) -> Type[BaseGenerator] | List[Type[BaseGenerator]]:
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
