from gameplay.greats.core.engineers._base import CoreBaseGreatEngineer
from managers.i18n import _t


class VintBob(CoreBaseGreatEngineer):
    def __init__(self):
        super().__init__(
            key="core.engineers.vint_bob",
            name=_t("content.greats.core.people.vint_bob.name"),
            description=_t("content.greats.core.people.vint_bob.description"),
            cost=100,
        )
