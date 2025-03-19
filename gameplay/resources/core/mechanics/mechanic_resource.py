from gameplay.resource import BaseResource, ResourceValueType, ResourceTypeMechanic
from typing import Type


class MechanicsStrategyResource(BaseResource):
    type: Type[ResourceTypeMechanic] = ResourceTypeMechanic
    configure_as_float_or_int: ResourceValueType = ResourceValueType.FLOAT


class MechanicBaseResource(MechanicsStrategyResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BaseGreatMechanicResource(MechanicsStrategyResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
