from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ScientificTheory(Tech):
    key = "core.scientific_theory"
    name = t_("tech.scientific_theory.name")
    description = t_("tech.scientific_theory.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
