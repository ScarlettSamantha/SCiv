from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeStrategic, ResourceValueType

from managers.i18n import _t


class Coal(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.strategic.coal",
            _t("content.resources.core.coal"),
            value,
            ResourceTypeStrategic,
            ResourceValueType.INT,
        )
