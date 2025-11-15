from typing import TYPE_CHECKING, Any, cast
from weakref import ReferenceType

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


class FinishResearch(DebugAction):
    key = "actions.debug.finish_research"
    debug_action = True
    category = "City"

    def __init__(self):
        super().__init__(
            name=self.key,
            action=self.run,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=None,
        )
        self.on_the_spot_action = False
        self.targeting_tile_action = True
        self.tile: "Tile | None" = None

    def run(self, *args: Any, **kwargs: Any) -> None:
        self.tile: "Tile | None" = cast("Tile | None", self.action_kwargs.get("target", None))

        if self.tile is None:
            raise ValueError("Tile must be set before trying to change the type.")

        owner: "ReferenceType[Player] | Player | None" = self.tile.owner

        if owner is None:
            return

        player: Player | None = owner() if isinstance(owner, ReferenceType) else owner

        if player is None or player.tech.currently_researching() is None:
            return

        player.tech.complete_research()
        MessengerGlobal.messenger.send("ui.update.ui.refresh_top_bar")
