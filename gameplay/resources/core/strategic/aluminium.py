from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeStrategic, ResourceValueType

from managers.i18n import _t


class Aluminium(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.aluminium",
            _t("content.resources.core.aluminium"),
            value,
            ResourceTypeStrategic,
            ResourceValueType.INT,
        )
