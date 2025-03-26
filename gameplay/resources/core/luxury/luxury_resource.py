from typing import Type

from gameplay.resource import BaseResource, ResourceTypeLuxury, ResourceValueType


class BaseLuxuryResource(BaseResource):
    type: Type[ResourceTypeLuxury] = ResourceTypeLuxury
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    color = (1.0, 1.0, 0.0)
