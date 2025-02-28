from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Deer(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.deer",
            _t("content.resources.core.deer"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
