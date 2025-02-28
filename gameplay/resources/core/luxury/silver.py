from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Silver(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.luxury.silver",
            _t("content.resources.core.silver"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
