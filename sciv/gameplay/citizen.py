from typing import Any


class Citizen:
    def __init__(self):
        self.name: str = "Citizen"
        self.experience: int = 0
        self.is_alive: bool = True
        self.is_active: bool = True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "experience": self.experience,
            "is_alive": self.is_alive,
            "is_active": self.is_active,
        }

    def load_state(self, state: dict[str, Any]) -> None:
        self.name = state.get("name", "Citizen")
        self.experience = state.get("experience", 0)
        self.is_alive = state.get("is_alive", True)
        self.is_active = state.get("is_active", True)
