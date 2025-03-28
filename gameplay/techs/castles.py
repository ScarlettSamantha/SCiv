from gameplay.tech import Tech
from managers.i18n import _t


class Castles(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.castles",
            _t("tech.castles.name"),
            _t("tech.castles.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
