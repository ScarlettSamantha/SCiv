from gameplay.tech import Tech
from managers.i18n import _t


class Cartography(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.cartography",
            _t("tech.cartography.name"),
            _t("tech.cartography.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
