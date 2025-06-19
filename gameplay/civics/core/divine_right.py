from typing import Any, Optional


from gameplay.civic import Civic
from gameplay.improvement import Improvement
from managers.i18n import t_
from gameplay.effects.civics.divine_right import DivineRightEffect


class DivineRight(Civic):
    key = "core.culture.civics.divine_right"
    name = t_("content.culture.civics.core.divine_right.name")
    description = t_("content.culture.civics.core.divine_right.description")

    unlocks_entities = [
        DivineRightEffect,
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    def on_complete(self):
        from gameplay.improvements.core.city.palace import Palace

        palace: Optional[Improvement] = self.get_player().get_capital().get_improvements().get(Palace)
        if palace is None or not isinstance(palace, Palace):
            return super().on_complete()

        DivineRightEffect.apply_to_entity(palace, self.get_player())

        return super().on_complete()
