from gameplay.culture import Civic
from managers.i18n import _t


class PhilosophicalDiscourse(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.philosophical_discourse",
            name=_t("content.culture.civics.core.philosophical_discourse.name"),
            description=_t("content.culture.civics.core.philosophical_discourse.description"),
            *args,
            **kwargs,
        )
