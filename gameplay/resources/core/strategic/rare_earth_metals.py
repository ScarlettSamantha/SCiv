from __future__ import annotations
from gameplay.resource import BaseResource, ResourceTypeStrategic, ResourceValueType

from managers.i18n import _t


class RareEarthMetals(BaseResource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.strategic.rare_earth_metals",
            _t("content.resources.core.rare_earth_metals"),
            value,
            ResourceTypeStrategic,
            ResourceValueType.INT,
        )
