from typing import Any

from managers.i18n import t_

from gameplay.units.core.classes.civilian._base import CoreCivilianBaseClass
from gameplay.promotion import Promotion, PromotionTree
from system.actions import Action
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

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.class.settler",
            name="content.units.core.units.civilian.settler.name",
            description=t_("content.units.core.units.civilian.settler.description"),
            icon=None,
            promotion_tree=SettlerPromotionTree(),
            model_rotation=(0, 0, 0),
            model_size=0.2,
            model_position_offset=(0, 0, 0.1),
            *args,
            **kwargs,
        )
        self.max_moves

    def founding_conditions(self, _) -> bool:
        if self.tile.is_city() is False or self.tile.owner != self.owner or not self.tile.is_passable():
            return False
        return True

    def _register(self):
        found_action = Action(
            name=t_("actions.unit.found_city"),
            action=self.found_city,
            condition=self.founding_conditions,
            on_failure=lambda action, args, kwargs: None,
        )
        found_action.on_the_spot_action = True
        found_action.remove_actions_after_use = True
        self.actions.append(found_action)

        walk_action = Action(
            name=t_("actions.unit.move"),
            action=self.move,
            condition=self.can_move,
            on_failure=lambda action, args, kwargs: None,
        )
        walk_action.on_the_spot_action = False
        walk_action.targeting_tile_action = True
        self.actions.append(walk_action)

        return super()._register()

    def found_city(self, _, *args, **kwargs):
        self.tile.found(self.owner)
        self.destroy()
        return True
