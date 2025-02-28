from gameplay.resource import BaseResource, ResourceValueType, ResourceTypeBonus
from typing import Type


class BasicBaseResource(BaseResource):
    type: Type[ResourceTypeBonus] = ResourceTypeBonus
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT
