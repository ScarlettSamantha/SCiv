from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class MountainTunnel(Improvement):
    name = t_("content.improvements.core.general.mountain_tunnel.name")
    description = t_("content.improvements.core.general.mountain_tunnel.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="mountain_tunnel", food=1.0, mode=Yields.ADDITIVE)
