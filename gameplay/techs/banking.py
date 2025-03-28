from gameplay.tech import Tech
from managers.i18n import _t


class Banking(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.banking",
            _t("tech.banking.name"),
            _t("tech.banking.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
