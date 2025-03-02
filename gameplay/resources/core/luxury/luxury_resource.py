from gameplay.resource import BaseResource, ResourceValueType, ResourceTypeLuxury
from typing import Type


class BaseLuxuryResource(BaseResource):
    type: Type[ResourceTypeLuxury] = ResourceTypeLuxury
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
