from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Salt(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.salt",
            _t("content.resources.core.salt"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
