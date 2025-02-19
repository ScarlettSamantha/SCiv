from __future__ import annotations
from gameplay.tech import Tech
from managers.i18n import _t


class NuclearFission(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.nuclear_fission",
            _t("tech.nuclear_fission.name"),
            _t("tech.nuclear_fission.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
