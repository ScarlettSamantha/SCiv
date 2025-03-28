from gameplay.tech import Tech
from managers.i18n import _t


class Mathematics(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.mathematics",
            _t("tech.mathematics.name"),
            _t("tech.mathematics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
