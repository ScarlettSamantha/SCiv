from gameplay.resource import BaseResource, ResourceType, ResourceValueType


class BaseBonusResource(BaseResource):
    type = ResourceType.BONUS
    configure_as_float_or_int: ResourceValueType = ResourceValueType.INT
    _color = (1.0, 0.0, 1.0)
