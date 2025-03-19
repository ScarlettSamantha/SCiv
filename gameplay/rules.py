from abc import ABC, abstractmethod
from typing import Dict, Literal


class GameRules(ABC):
    def __init__(self): ...

    @classmethod
    @abstractmethod
    def get_city_founding_distance_rule(cls) -> int: ...

    @classmethod
    @abstractmethod
    def get_city_founding_in_own_territory_rule(cls) -> bool: ...

    @classmethod
    @abstractmethod
    def get_unit_looses_movement_after_building_rule(cls) -> bool: ...

    @classmethod
    def get_rules(cls) -> Dict[str, int]:
        return {
            "city_founding_distance": cls.get_city_founding_distance_rule(),
            "city_founding_in_own_territory": cls.get_city_founding_in_own_territory_rule(),
        }


class SCIVRules(GameRules):
    @classmethod
    def get_city_founding_distance_rule(cls) -> int | Literal[2]:
        return 2

    @classmethod
    def get_city_founding_in_own_territory_rule(cls) -> bool | Literal[True]:
        return True

    @classmethod
    def get_unit_looses_movement_after_building_rule(cls) -> bool | Literal[True]:
        return True


global active_game_rules


def set_game_rules(rules: GameRules):
    global active_game_rules
    active_game_rules = rules


def get_game_rules() -> GameRules:
    return active_game_rules
