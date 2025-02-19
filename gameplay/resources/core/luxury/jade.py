from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Jade(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.luxury.jade",
            _t("content.resources.core.jade"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
