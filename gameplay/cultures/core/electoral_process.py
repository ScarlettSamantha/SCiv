from gameplay.culture import Civic
from managers.i18n import _t


class ElectoralProcess(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.electoral_process",
            name=_t("content.culture.civics.core.electoral_process.name"),
            description=_t("content.culture.civics.core.electoral_process.description"),
            *args,
            **kwargs,
        )
