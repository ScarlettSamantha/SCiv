from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Copper(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.copper",
            _t("content.resources.core.copper"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
