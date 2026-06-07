from typing import Any

from gameplay.actions.debug.debug_action import DebugAction
from managers.game import Game


class RevealMap(DebugAction):
    key = "actions.debug.reveal_map"
    debug_action = True
    category = "Map"

    def __init__(self) -> None:
        super().__init__(
            name=self.key,
            action=self.run,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=None,
        )

        self.on_the_spot_action = True
        self.targeting_tile_action = False

    def run(self, *args: Any, **kwargs: Any) -> None:
        game: Game = Game.get_singleton_instance()
        game.debug_reveal_map_for_session_player()
