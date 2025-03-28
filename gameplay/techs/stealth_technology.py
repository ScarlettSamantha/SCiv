from gameplay.tech import Tech
from managers.i18n import _t


class StealthTechnology(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.stealth_technology",
            _t("tech.stealth_technology.name"),
            _t("tech.stealth_technology.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
