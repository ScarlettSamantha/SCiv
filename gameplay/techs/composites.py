from gameplay.tech import Tech
from managers.i18n import _t


class Composites(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.composites",
            _t("tech.composites.name"),
            _t("tech.composites.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
