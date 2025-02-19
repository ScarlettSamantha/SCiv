from __future__ import annotations
from gameplay.tech import Tech
from managers.i18n import _t


class Nanotechnology(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.nanotechnology",
            _t("tech.nanotechnology.name"),
            _t("tech.nanotechnology.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
