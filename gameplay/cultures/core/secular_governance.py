from gameplay.culture import Civic
from managers.i18n import _t


class SecularGovernance(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.secular_governance",
            name=_t("content.culture.civics.core.secular_governance.name"),
            description=_t("content.culture.civics.core.secular_governance.description"),
            *args,
            **kwargs,
        )
