from typing import Type

from gameplay.resource import BaseResource


class BasicBaseResource(BaseResource):
    from gameplay.resource import ResourceValueType, ResourceTypeBonus

    type: Type[ResourceTypeBonus] = ResourceTypeBonus
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT
