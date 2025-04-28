from typing import TypeVar

from gameplay.resource import BaseResource, ResourceTypeBasic

BasicResourceType = TypeVar("BasicResourceType", bound="BasicBaseResource")


class BasicBaseResource(BaseResource):
    from gameplay.resource import ResourceValueType

    type = ResourceTypeBasic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT
