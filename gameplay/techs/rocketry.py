from gameplay.tech import Tech
from managers.i18n import _t


class Rocketry(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.rocketry",
            _t("tech.rocketry.name"),
            _t("tech.rocketry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
