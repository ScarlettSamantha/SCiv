from typing import Type, TypeVar

from gameplay.resource import BaseResource


class BasicBaseResource(BaseResource):
    from gameplay.resource import ResourceTypeBonus, ResourceValueType

    type: Type[ResourceTypeBonus] = ResourceTypeBonus
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT


BasicResourceType = TypeVar("BasicResourceType", bound=BasicBaseResource)
