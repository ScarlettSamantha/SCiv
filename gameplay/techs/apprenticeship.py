from gameplay.tech import Tech
from managers.i18n import _t


class Apprenticeship(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.apprenticeship",
            _t("tech.apprenticeship.name"),
            _t("tech.apprenticeship.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
