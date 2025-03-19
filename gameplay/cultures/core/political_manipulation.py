from gameplay.culture import Civic
from managers.i18n import _t


class PoliticalManipulation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.political_manipulation",
            name=_t("content.culture.civics.core.political_manipulation.name"),
            description=_t("content.culture.civics.core.political_manipulation.description"),
            *args,
            **kwargs,
        )
