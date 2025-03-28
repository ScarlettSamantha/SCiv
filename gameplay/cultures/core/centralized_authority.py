from gameplay.culture import Civic
from managers.i18n import _t


class CentralizedAuthority(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.centralized_authority",
            name=_t("content.culture.civics.core.centralized_authority.name"),
            description=_t("content.culture.civics.core.centralized_authority.description"),
            *args,
            **kwargs,
        )
