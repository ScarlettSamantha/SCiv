from gameplay.tech import Tech
from managers.i18n import _t


class Archery(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.archery",
            _t("tech.archery.name"),
            _t("tech.archery.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
