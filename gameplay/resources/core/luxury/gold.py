from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Gold(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.luxury.gold",
            _t("content.resources.core.gold"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
