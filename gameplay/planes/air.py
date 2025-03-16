from typing import Any

from gameplay.planes.plane import Plane
from managers.i18n import t_


class Air(Plane):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            key="core.plane.air",
            name=t_("content.planes.core.air.name"),
            description=t_("content.planes.core.air.description"),
            *args,
            **kwargs,
        )
