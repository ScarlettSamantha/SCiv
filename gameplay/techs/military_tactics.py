from gameplay.tech import Tech
from managers.i18n import _t


class MilitaryTactics(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.military_tactics",
            _t("tech.military_tactics.name"),
            _t("tech.military_tactics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
