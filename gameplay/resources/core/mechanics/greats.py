from typing import Dict, Type

from gameplay.resources.core.mechanics.mechanic_resource import BaseGreatMechanicResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, t_


class GreatScientist(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great.scientist"
    name: T_TranslationOrStr = t_("content.greats.core.trees.scientists.name")
    description: T_TranslationOrStr = t_("content.greats.core.trees.scientists.description")
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatArtist(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_artist"
    name = t_("content.resources.great_person_culture.name")
    description = t_("content.resources.great_person_culture.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatHero(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_hero"
    name = t_("content.resources.great_person_hero.name")
    description = t_("content.resources.great_person_hero.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatHoly(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_holy"
    name = t_("content.resources.great_person_faith.name")
    description = t_("content.resources.great_person_faith.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatMilitary(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_military"
    name = t_("content.resources.great_person_military.name")
    description = t_("content.resources.great_person_military.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatEngineer(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_engineer"
    name = t_("content.resources.great_person_engineer.name")
    description = t_("content.resources.great_person_engineer.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatCommerece(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_commerece"
    name = t_("content.resources.great_person_commerece.name")
    description = t_("content.resources.great_person_commerece.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)


class GreatExplorer(BaseGreatMechanicResource):
    key: str = "resource.core.mechanic.great_person_explorer"
    name = t_("content.resources.great_person_explorer.name")
    description = t_("content.resources.great_person_explorer.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)
