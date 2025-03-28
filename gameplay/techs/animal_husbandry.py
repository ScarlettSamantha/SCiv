from gameplay.tech import Tech
from managers.i18n import _t


class AnimalHusbandry(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.animal_husbandry",
            _t("tech.animal_husbandry.name"),
            _t("tech.animal_husbandry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
