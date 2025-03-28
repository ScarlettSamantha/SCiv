from gameplay.tech import Tech
from managers.i18n import _t


class SquareRigging(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.square_rigging",
            _t("tech.square_rigging.name"),
            _t("tech.square_rigging.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
