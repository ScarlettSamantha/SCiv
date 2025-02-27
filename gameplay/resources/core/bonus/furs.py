from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeBonus, ResourceValueType

from managers.i18n import _t


class Furs(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.furs",
            _t("content.resources.core.furs"),
            value,
            ResourceTypeBonus,
            ResourceValueType.INT,
        )
