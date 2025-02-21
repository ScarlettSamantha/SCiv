from random import choice
from system.pyload import PyLoad
from gameplay.civilization import Civilization as BaseCivilization
from typing import List, Type


class Civilization:
    @classmethod
    def all(cls) -> List[Type[BaseCivilization]]:
        classes = PyLoad.load_classes(
            "gameplay/civilizations", base_classes=BaseCivilization
        )
        for _, _class in classes.items():
            # Remove the base class from the list.
            if _class == BaseCivilization:
                del classes[_class]

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
