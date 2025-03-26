from typing import Type

from gameplay.resource import BaseResource, ResourceTypeBonus, ResourceValueType


class BaseBonusResource(BaseResource):
    type: Type[ResourceTypeBonus] = ResourceTypeBonus
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    color = (1.0, 0.0, 1.0)
