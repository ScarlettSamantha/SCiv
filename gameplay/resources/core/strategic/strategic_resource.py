from gameplay.resource import BaseResource, ResourceTypeStrategic, ResourceValueType


class BaseStrategicResource(BaseResource):
    type = ResourceTypeStrategic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    _color = (1.0, 0.0, 0.0)
