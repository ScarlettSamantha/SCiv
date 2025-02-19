from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeLuxury, ResourceValueType

from managers.i18n import _t


class Cats(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.cats",
            _t("content.resources.core.cats"),
            value,
            ResourceTypeLuxury,
            ResourceValueType.INT,
        )
