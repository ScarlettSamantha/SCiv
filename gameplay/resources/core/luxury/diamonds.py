from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Diamonds(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.luxury.diamonds",
            _t("content.resources.core.diamonds"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
