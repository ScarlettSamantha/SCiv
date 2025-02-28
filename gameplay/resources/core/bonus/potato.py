from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Potato(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.potato",
            _t("content.resources.core.potato"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
