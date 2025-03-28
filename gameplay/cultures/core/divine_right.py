from gameplay.culture import Civic
from managers.i18n import _t


class DivineRight(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.divine_right",
            name=_t("content.culture.civics.core.divine_right.name"),
            description=_t("content.culture.civics.core.divine_right.description"),
            *args,
            **kwargs,
        )
