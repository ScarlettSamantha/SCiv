from gameplay.resource import BaseResource, ResourceTypeLuxury, ResourceValueType


class BaseLuxuryResource(BaseResource):
    type = ResourceTypeLuxury
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    _color = (1.0, 1.0, 0.0)
