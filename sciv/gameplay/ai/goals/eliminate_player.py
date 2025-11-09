from typing import TYPE_CHECKING, Any, Dict

from gameplay.ai.core import Goal
from gameplay.player import Player

if TYPE_CHECKING:
    from gameplay.ai.goal import T_PARENT, T_TARGET


class EliminatePlayer(Goal):
    name = "Eliminate Player Goal"
    description = "Eliminate a specific player"

    def __init__(self, parent: "T_PARENT", target: "T_TARGET", *args: Dict[str, Any], **kwargs: Dict[str, Any]) -> None:
        super().__init__(parent, target, executing_unit=None, *args, **kwargs)
        self.name: str = "Eliminate Player"
        self.description: str = f"Eliminate the player {str(self.get_target().name)}"

    def turn_tick(self) -> None:
        super().turn_tick()

    def get_player(self) -> "Player":
        return self.target  # type: ignore[return-value]

    def calculate_if_achieved(self) -> bool:
        return self.get_player().is_alive() is False
