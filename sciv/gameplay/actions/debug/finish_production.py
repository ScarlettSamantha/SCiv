from typing import TYPE_CHECKING, Any, cast

from gameplay.actions.debug.debug_action import DebugAction
from gameplay.city import City

if TYPE_CHECKING:
    from gameplay.tile import Tile


class FinishProduction(DebugAction):
    key = "actions.debug.finish_production"
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

        if self.tile.owner is None:
            return

        city: City | None = self.tile.city
        if city is None:
            return

        city.finish_production()
