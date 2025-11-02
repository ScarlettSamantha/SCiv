from typing import TYPE_CHECKING, Any

from gameplay.city import EntityType
from gameplay.condition import Conditions, ResearchCondition
from gameplay.promotion import Promotion, PromotionTree
from gameplay.units.core.classes.civilian._base import CoreCivilianBaseClass
from managers.i18n import t_
from system.requires import RequiresPromotionTreeUnlocked

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


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
    _model = "assets/models/units/settler_cart.glb"
    buildable = True
    key = "core.unit.class.settler"
    name = t_("content.units.core.units.civilian.settler.name")
    description = t_("content.units.core.units.civilian.settler.description")
    icon = "assets/icons/default/units/settler.png"
    promotion_tree = SettlerPromotionTree
    model_size = 0.50

    def __init__(self, tile: "Tile", player: "Player", *args: Any, **kwargs: Any):
        super().__init__(
            tile,
            player,
            *args,
            **kwargs,
        )
        from gameplay.techs.pottery import Pottery

        self.entity_type_ref = EntityType.UNIT.value
        self.build_conditions = Conditions(ResearchCondition(tech=Pottery, player=player))
        self.model_rotation = (0, 0, 0)
        self.model_position_offset = (0, 0, 0.0)
        self.unit_icons_z_offset = 1.5

    def register_actions(self):
        super().register_actions()
        from gameplay.actions.unit.found import FoundAction

        self.actions.append(FoundAction(self))

    @classmethod
    def on_tooltip(cls) -> str:
        return str(t_("content.units.core.units.civilian.settler.tooltip"))
