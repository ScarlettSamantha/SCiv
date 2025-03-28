from gameplay.culture import Civic
from managers.i18n import _t


class StatePropaganda(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.state_propaganda",
            name=_t("content.culture.civics.core.state_propaganda.name"),
            description=_t("content.culture.civics.core.state_propaganda.description"),
            *args,
            **kwargs,
        )
