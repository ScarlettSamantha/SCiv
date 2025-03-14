from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class MountainTunnel(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.general.mountain_tunnel",
            _t("content.improvements.core.general.mountain_tunnel.name"),
            _t("content.improvements.core.general.mountain_tunnel.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="mountain_tunnel", food=1.0, mode=Yields.ADDITIVE)
