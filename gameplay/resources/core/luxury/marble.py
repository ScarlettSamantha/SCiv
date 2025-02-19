from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Marble(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.luxury.marble",
            _t("content.resources.core.marble"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
