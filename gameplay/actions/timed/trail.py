from typing import Any

from gameplay.actions.timed.base_timed_action import BaseTimedAction
from gameplay.tiles.base_tile import Tile
from helpers.colors import Colors
from managers.i18n import t_


class Trial(BaseTimedAction):
    def __init__(self, delay: int = 5, *args: Any, **kwargs: Any):
        if "tile" not in kwargs:
            raise ValueError("Tile must be passed to the trail action")

        self.tile: Tile = kwargs.pop("tile")  # type: ignore

        super().__init__(
            delay=delay,  # 15 default seconds then the trail will disappear
            name=f"{t_('passive.unit.trail')}_{self.tile.x}_{self.tile.y}",
            action=self.restore_tile,  # restore the tile color in about 5 seconds
            on_invoke=self.color_tile,  # color the tile to purple
            *args,
            **kwargs,
        )

        self.on_the_spot_action = True
        self.targeting_tile_action = False

    def color_tile(self, *args: Any, **kwargs: Any):
        self.tile.set_color(Colors.PURPLE[:3] + (0.8,))

    def restore_tile(self, *args: Any, **kwargs: Any) -> bool:
        self.tile.set_color(Colors.RESTORE)
        return True
