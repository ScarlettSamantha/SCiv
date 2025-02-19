from __future__ import annotations
from gameplay.tech import Tech
from managers.i18n import _t


class Stirrups(Tech):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.stirrups",
            _t("tech.stirrups.name"),
            _t("tech.stirrups.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
