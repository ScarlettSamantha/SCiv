from typing import Any

from gameplay.promotion import Promotion, PromotionTree
from gameplay.units.core.classes.civilian._base import CoreCivilianBaseClass
from managers.i18n import t_
from system.requires import RequiresPromotionTreeUnlocked


class SettlerPromotion(Promotion):
    pass


class Caravan(SettlerPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.caravan",
            name=t_("content.units.core.promotions.settler.caravan.name"),
            description=t_("content.units.core.promotions.settler.caravan.description"),
            icon="",
            *args,
            **kwargs,
        )


class Generational(SettlerPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.generational",
            name=t_("content.units.core.promotions.settler.generational.name"),
            description=t_("content.units.core.promotions.settler.generation.description"),
            icon="",
            *args,
            **kwargs,
        )


class SettlerPromotionTree(PromotionTree):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            key="core.unit.promotion.tree.builder",
            name="",
            description="",
            icon="",
            *args,
            **kwargs,
        )

    def register_promotions(self):
        caravan = Caravan()
        generation = Generational()

        caravan.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        generation.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)

        self.add_promotion(caravan)
        self.add_promotion(generation)


class Settler(CoreCivilianBaseClass):
    _model = "assets/models/units/pessent.glb"
    buildable = True
    key = "core.unit.class.settler"
    name = t_("content.units.core.units.civilian.settler.name")
    description = t_("content.units.core.units.civilian.settler.description")
    icon = None
    promotion_tree = SettlerPromotionTree
    model_size = 0.2

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
        self.model_rotation = (0, 0, 0)
        self.model_position_offset = (0, 0, 0.1)

    def register_actions(self):
        from gameplay.actions.unit.found import FoundAction

        self.actions.append(FoundAction(self))

        from gameplay.actions.unit.move import WalkAction

        self.actions.append(WalkAction(self))

        super().register_actions()
