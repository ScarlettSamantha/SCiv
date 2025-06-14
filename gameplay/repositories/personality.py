from random import choice
from typing import List, Type

from gameplay.personalities.base import BasePersonality
from system.pyload import PyLoad


class PersonalityRepository:
    @classmethod
    def all(cls) -> List[Type[BasePersonality]]:
        classes = PyLoad.load_classes(
            "gameplay/personalities", base_classes=BasePersonality, package="gameplay.personalities"
        )
        for key, _class in list(classes.items()):
            if _class == BasePersonality:
                classes.pop(key)
        return list(classes.values())

    @classmethod
    def random(cls, num: int = 1, unique: bool = False) -> Type[BasePersonality] | List[Type[BasePersonality]]:
        _selected_personalities: List[Type[BasePersonality]] = []

        items = cls.all()
        for _ in range(num):
            while True:
                if len(items) == 0:
                    _selected_personality: Type[BasePersonality] = BasePersonality
                else:
                    _selected_personality: Type[BasePersonality] = choice(items)

                if unique and _selected_personality in _selected_personalities:
                    continue

                _selected_personalities.append(_selected_personality)
                break

            if num == 1:
                return _selected_personality  # type: ignore

        return _selected_personalities
