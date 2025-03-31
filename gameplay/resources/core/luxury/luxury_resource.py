from gameplay.resource import BaseResource, ResourceType, ResourceValueType


class BaseLuxuryResource(BaseResource):
    type = ResourceType.LUXURY
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    _color = (1.0, 1.0, 0.0)
