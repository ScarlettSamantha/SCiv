from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class SyntheticMaterials(Tech):
    key = "core.synthetic_materials"
    name = t_("tech.synthetic_materials.name")
    description = t_("tech.synthetic_materials.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
