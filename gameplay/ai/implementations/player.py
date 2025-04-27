from gameplay.ai.core import AI
from gameplay.ai.goal import Goals
from gameplay.player import Player


class PlayerAI(AI):
    """
    PlayerAI is a subclass of AI that represents the AI that helps the player by optionally auto managing things.
    It can manage the player's units, cities, tiles, goals, memory, tasks, and personality.
    """

    def __init__(self, player: Player):
        super().__init__(player)

    def register_end_goal(self) -> Goals:
        return Goals()

    def register_goals(self) -> Goals:
        return Goals()

    def on_turn_end(self) -> None: ...

    def on_turn_start(self) -> None: ...

    def on_game_end(self) -> None: ...

    def on_game_start(self) -> None: ...
