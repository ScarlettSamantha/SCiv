from typing import TypeVar

from gameplay.resource import BaseResource, ResourceType

BasicResourceType = TypeVar("BasicResourceType", bound="BasicBaseResource")


class BasicBaseResource(BaseResource):
    from gameplay.resource import ResourceValueType

    type = ResourceType.BASIC
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT
