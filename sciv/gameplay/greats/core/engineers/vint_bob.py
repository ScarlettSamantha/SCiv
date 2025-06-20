from gameplay.greats.core.engineers._base import CoreBaseGreatEngineer
from managers.i18n import t_


class VintBob(CoreBaseGreatEngineer):
    def __init__(self):
        super().__init__(
            key="core.engineers.vint_bob",
            name=t_("content.greats.core.people.vint_bob.name"),
            description=t_("content.greats.core.people.vint_bob.description"),
            cost=100,
        )
