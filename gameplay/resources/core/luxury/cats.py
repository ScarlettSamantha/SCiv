from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Cats(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.cats",
            _t("content.resources.core.cats"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
