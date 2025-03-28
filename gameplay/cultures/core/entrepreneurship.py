from gameplay.culture import Civic
from managers.i18n import _t


class Entrepreneurship(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.entrepreneurship",
            name=_t("content.culture.civics.core.entrepreneurship.name"),
            description=_t("content.culture.civics.core.entrepreneurship.description"),
            *args,
            **kwargs,
        )
