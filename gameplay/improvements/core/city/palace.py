from typing import Type

from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.yields import Yields
from managers.i18n import t_


class Palace(BaseCityImprovement):
    name = t_("content.improvements.core.city.palace.name")
    description = t_("content.improvements.core.city.palace.description")
    placeable_on_city = True
    placeable_on_condition = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.amount_resource_needed = Yields(production=50)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = Yields(gold=2, production=2, food=2, science=2, culture=2, faith=2)
