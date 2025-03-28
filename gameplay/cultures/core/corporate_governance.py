from gameplay.culture import Civic
from managers.i18n import _t


class CorporateGovernance(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.corporate_governance",
            name=_t("content.culture.civics.core.corporate_governance.name"),
            description=_t("content.culture.civics.core.corporate_governance.description"),
            *args,
            **kwargs,
        )
