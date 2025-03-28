from gameplay.tech import Tech
from managers.i18n import _t


class ClayTablets(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.clay_tablets",
            _t("tech.clay_tablets.name"),
            _t("tech.clay_tablets.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
