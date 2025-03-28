from gameplay.tech import Tech
from managers.i18n import _t


class Industrialisation(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.industrialisation",
            _t("tech.industrialisation.name"),
            _t("tech.industrialisation.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
