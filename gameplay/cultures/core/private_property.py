from gameplay.culture import Civic
from managers.i18n import _t


class PrivateProperty(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.private_property",
            name=_t("content.culture.civics.core.private_property.name"),
            description=_t("content.culture.civics.core.private_property.description"),
            *args,
            **kwargs,
        )
