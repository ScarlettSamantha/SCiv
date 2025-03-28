from gameplay.tech import Tech
from managers.i18n import _t


class Sanitation(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.sanitation",
            _t("tech.sanitation.name"),
            _t("tech.sanitation.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
