from gameplay.culture import Civic
from managers.i18n import _t


class SocialWelfare(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.social_welfare",
            name=_t("content.culture.civics.core.social_welfare.name"),
            description=_t("content.culture.civics.core.social_welfare.description"),
            *args,
            **kwargs,
        )
