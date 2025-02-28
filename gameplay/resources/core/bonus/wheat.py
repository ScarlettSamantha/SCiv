from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Wheat(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.wheat",
            _t("content.resources.core.wheat"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
