from typing import Any

from gameplay.resource import BaseResource, ResourceTypeMechanic, ResourceValueType


class MechanicsStrategyResource(BaseResource):
    type = ResourceTypeMechanic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT


class MechanicBaseResource(MechanicsStrategyResource):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class BaseGreatMechanicResource(MechanicsStrategyResource):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
