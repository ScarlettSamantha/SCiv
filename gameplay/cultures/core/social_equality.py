from gameplay.culture import Civic
from managers.i18n import _t


class SocialEquality(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.social_equality",
            name=_t("content.culture.civics.core.social_equality.name"),
            description=_t("content.culture.civics.core.social_equality.description"),
            *args,
            **kwargs,
        )
