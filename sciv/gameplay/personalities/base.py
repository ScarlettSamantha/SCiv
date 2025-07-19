from abc import ABC
from typing import Any


class BasePersonality(ABC):
    name: str = "Base Personality"

    def __init__(self):
        pass

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    def load_state(self, state: dict[str, Any]) -> None:
        self.name = state.get("name", self.name)
