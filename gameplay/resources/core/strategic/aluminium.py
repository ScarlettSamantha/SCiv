from __future__ import annotations
from gameplay.resource import Resource, ResourceTypeStrategic, ResourceValueType

from managers.i18n import _t


class Aluminium(Resource):
    def __init__(self, value: int = 0):
        super().__init__(
            "core.bonus.aluminium",
            _t("content.resources.core.aluminium"),
            value,
            ResourceTypeStrategic,
            ResourceValueType.INT,
        )
