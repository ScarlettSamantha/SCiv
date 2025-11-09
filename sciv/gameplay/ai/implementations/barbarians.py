from typing import TYPE_CHECKING

from gameplay.ai.core import AI
from gameplay.ai.goal import Goals

if TYPE_CHECKING:
    from gameplay.player import Player


class BarbariansAI(AI):
    def __init__(self, player: "Player"):
        super().__init__(player)

    def register_end_goal(self) -> Goals:
        return Goals()

    def register_goals(self) -> Goals:
        return Goals()

    def on_turn_end(self) -> None: ...

    def on_turn_start(self) -> None: ...

    def on_game_end(self) -> None: ...
    def on_game_start(self) -> None: ...
