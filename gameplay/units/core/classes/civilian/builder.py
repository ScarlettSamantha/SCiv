from typing import Any

from gameplay.promotion import Promotion, PromotionTree
from gameplay.units.core.classes.civilian._base import CoreCivilianBaseClass
from managers.i18n import t_
from system.requires import RequiresPromotionComplete, RequiresPromotionTreeUnlocked


class BuilderPromotion(Promotion):
    pass


class Farmer(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.farmer",
            name=t_("content.units.core.promotions.builder.farmer.name"),
            description=t_("content.units.core.promotions.builder.farmer.description"),
            *args,
            **kwargs,
        )


class Miner(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.miner",
            name=t_("content.units.core.promotions.builder.miner.name"),
            description=t_("content.units.core.promotions.builder.miner.description"),
            *args,
            **kwargs,
        )


class Lumberjack(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.lumberjack",
            name=t_("content.units.core.promotions.builder.lumberjack.name"),
            description=t_("content.units.core.promotions.builder.lumberjack.description"),
            *args,
            **kwargs,
        )


class Fisherman(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.fisherman",
            name=t_("content.units.core.promotions.builder.fisherman.name"),
            description=t_("content.units.core.promotions.builder.fisherman.description"),
            *args,
            **kwargs,
        )


class Hunter(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.hunter",
            name=t_("content.units.core.promotions.builder.hunter.name"),
            description=t_("content.units.core.promotions.builder.hunter.description"),
            *args,
            **kwargs,
        )


class Electrician(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.electrician",
            name=t_("content.units.core.promotions.builder.electrician.name"),
            description=t_("content.units.core.promotions.builder.electrician.description"),
            *args,
            **kwargs,
        )


class RenewableEnergy(BuilderPromotion):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.unit.promotion.renewable_energy",
            name=t_("content.units.core.promotions.builder.renewable_energy.name"),
            description=t_("content.units.core.promotions.builder.renewable_energy.description"),
            *args,
            **kwargs,
        )


class BuilderPromotionTree(PromotionTree):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(key="core.unit.promotion.tree.builder", *args, **kwargs)

    def register_promotions(self):
        farmer = Farmer()
        miner = Miner()
        lumberjack = Lumberjack()
        fisherman = Fisherman()
        hunter = Hunter()
        electrician = Electrician()
        renewable_energy = RenewableEnergy()

        farmer.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        miner.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        lumberjack.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        fisherman.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        hunter.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        electrician.requires = RequiresPromotionTreeUnlocked(promotion_tree=self)
        renewable_energy.requires = RequiresPromotionComplete(promotion=electrician)

        self.add_promotion(farmer)
        self.add_promotion(miner)
        self.add_promotion(lumberjack)
        self.add_promotion(fisherman)
        self.add_promotion(hunter)
        self.add_promotion(electrician)
        self.add_promotion(renewable_energy)


class Builder(CoreCivilianBaseClass):
    _model = "assets/models/units/peasant.glb"
    buildable = True
    key = "core.unit.class.builder"
    name = t_("content.units.core.units.civilian.builder.name")
    description = t_("content.units.core.units.civilian.builder.description")
    model_size = 0.2

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
        self.model_rotation = (0, 0, 0)
        self.model_position_offset = (0, 0, 0.1)
        self.can_build = True

        self.build_charges: int = 3
        self.build_charges_left: int = 3

    def register_actions(self):
        from gameplay.actions.unit.move import WalkAction

        self.add_action(WalkAction(self))

        return super().register_actions()
