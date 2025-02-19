from __future__ import annotations

from gameplay.planes.plane import Plane
from managers.i18n import t_
from typing import Any


class Naval(Plane):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            key="core.plane.naval",
            name=t_("content.planes.core.naval.name"),
            description=t_("content.planes.core.naval.description"),
            *args,
            **kwargs,
        )
