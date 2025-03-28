from gameplay.culture import Civic
from managers.i18n import _t


class SeperationChurchState(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.secularism",
            name=_t("content.culture.civics.core.secularism.name"),
            description=_t("content.culture.civics.core.secularism.description"),
            *args,
            **kwargs,
        )
