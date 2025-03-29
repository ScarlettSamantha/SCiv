from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ScientificTheory(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.scientific_theory",
            t_("tech.scientific_theory.name"),
            t_("tech.scientific_theory.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
