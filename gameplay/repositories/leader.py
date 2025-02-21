from random import choice
from typing import List, Type
from gameplay.leader import Leader as LeaderBaseObject
from system.pyload import PyLoad


class Leader:
    @classmethod
    def all(cls) -> List[Type[LeaderBaseObject]]:
        classes = PyLoad.load_classes("gameplay/leaders", base_classes=LeaderBaseObject)
        for key, _class in classes.items():
            if _class == LeaderBaseObject:
                del classes[key]
        return list(classes.values())

    @classmethod
    def random(
        cls, num: int = 1, unique: bool = False
    ) -> Type[LeaderBaseObject] | List[Type[LeaderBaseObject]]:
        _selected_leader: List[Type[LeaderBaseObject]] = []

        for _ in range(num):
            while True:
                _selected_personality: Type[LeaderBaseObject] = choice(cls.all())

                if unique and _selected_personality in _selected_leader:
                    continue

                _selected_leader.append(_selected_personality)
                break

            if num == 1:
                return _selected_personality

        return _selected_leader
