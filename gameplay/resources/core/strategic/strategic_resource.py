from gameplay.resource import BaseResource, ResourceValueType, ResourceTypeStrategic
from typing import Type


class BaseStrategyResource(BaseResource):
    type: Type[ResourceTypeStrategic] = ResourceTypeStrategic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
