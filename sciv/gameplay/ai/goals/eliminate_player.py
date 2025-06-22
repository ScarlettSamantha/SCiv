from typing import TYPE_CHECKING, Any, Dict

from gameplay.player import Player
from gameplay.ai.core import Goal

if TYPE_CHECKING:
    from gameplay.ai.goal import T_PARENT, T_TARGET


class EliminatePlayer(Goal):
    """
    EliminatePlayer is a goal that represents the AI's objective to eliminate a specific player.
    """

    name = "Eliminate Player Goal"
    description = "Eliminate a specific player"

    def __init__(self, parent: "T_PARENT", target: "T_TARGET", *args: Dict[str, Any], **kwargs: Dict[str, Any]) -> None:
        super().__init__(parent, target, executing_unit=None, *args, **kwargs)
        self.name: str = "Eliminate Player"
        self.description: str = f"Eliminate the player {str(self.get_target().name)}"

    def turn_tick(self) -> None:
        pass

    def get_player(self) -> "Player":
        return self.target  # type: ignore[return-value]
