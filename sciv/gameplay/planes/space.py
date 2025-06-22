from typing import Any

from gameplay.planes.plane import Plane
from managers.i18n import t_


class Space(Plane):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            key="core.plane.space",
            name=t_("content.planes.core.space.name"),
            description=t_("content.planes.core.space.description"),
            *args,
            **kwargs,
        )
