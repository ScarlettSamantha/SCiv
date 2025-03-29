from typing import Any, Type

from gameplay.resource import BaseResource, ResourceTypeMechanic, ResourceValueType


class MechanicsStrategyResource(BaseResource[ResourceTypeMechanic]):
    type: Type[ResourceTypeMechanic] = ResourceTypeMechanic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT


class MechanicBaseResource(MechanicsStrategyResource):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class BaseGreatMechanicResource(MechanicsStrategyResource):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
