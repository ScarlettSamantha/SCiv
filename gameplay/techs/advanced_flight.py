from gameplay.tech import Tech
from managers.i18n import _t


class AdvancedFlight(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.advanced_flight",
            _t("tech.advanced_flight.name"),
            _t("tech.advanced_flight.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
