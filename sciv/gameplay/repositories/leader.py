from random import choice
from typing import List, Type

from gameplay.civilization import Civilization as BaseCivilization
from gameplay.leader import Leader as LeaderBaseObject
from system.pyload import PyLoad


class Leader:
    leader_cache: List[Type[LeaderBaseObject]] = []

    @classmethod
    def _load_cache(cls) -> None:
        if not cls.leader_cache:
            cls.leader_cache = list(
                PyLoad.load_classes(directory="gameplay/leaders", base_classes=LeaderBaseObject).values()
            )

    @classmethod
    def all(cls) -> List[Type[LeaderBaseObject]]:
        if not cls.leader_cache:
            cls._load_cache()
        return cls.leader_cache

    @classmethod
    def for_civilization(cls, civ_cls: Type[BaseCivilization]) -> List[Type[LeaderBaseObject]]:
        cls._load_cache()

        civ_instance: BaseCivilization = civ_cls()  # type: ignore[call-arg]
        civ_leaders = getattr(civ_instance, "leaders", None)

        leaders_for_civ: List[Type[LeaderBaseObject]] = []

        if civ_leaders:
            for leader_obj in civ_leaders:
                leaders_for_civ.append(type(leader_obj))  # type: ignore
            return leaders_for_civ

        for leader_cls in cls.leader_cache:
            leader_civ = getattr(leader_cls, "civilization", None)
            if leader_civ is civ_cls:
                leaders_for_civ.append(leader_cls)

        return leaders_for_civ

    @classmethod
    def random(cls, num: int = 1, unique: bool = False) -> Type[LeaderBaseObject] | List[Type[LeaderBaseObject]]:
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
