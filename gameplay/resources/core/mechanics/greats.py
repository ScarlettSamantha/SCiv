from gameplay.resources.core.mechanics.mechanic_resource import BaseGreatMechanicResource
from managers.i18n import _t, T_TranslationOrStr
from typing import Tuple


class GreatScientist(BaseGreatMechanicResource):
    name: T_TranslationOrStr = _t("content.greats.core.trees.scientists.name")
    description: T_TranslationOrStr = _t("content.greats.core.trees.scientists.description")
    spawn_chance: float | Tuple[float, float] = 0
    spawn_amount: float | Tuple[float, float] = 0

    def __init__(self, value: int = 0):
        super().__init__("resource.core.mechanic.great.scientist", value=value)


class GreatArtist(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_culture.name")
    description = _t("content.resources.great_person_culture.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_culture", value=value)


class GreatHero(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_hero.name")
    description = _t("content.resources.great_person_hero.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_hero", value=value)


class GreatHoly(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_faith.name")
    description = _t("content.resources.great_person_faith.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_faith", value=value)


class GreatMilitary(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_military.name")
    description = _t("content.resources.great_person_military.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_military", value=value)


class GreatEngineer(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_engineer.name")
    description = _t("content.resources.great_person_engineer.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_engineer", value=value)


class GreatCommerece(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_commerece.name")
    description = _t("content.resources.great_person_commerece.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_commerece", value=value)


class GreatExplorer(BaseGreatMechanicResource):
    name = _t("content.resources.great_person_explorer.name")
    description = _t("content.resources.great_person_explorer.description")
    spawn_chance = 0
    spawn_amount = 0

    def __init__(self, value: int = 0):
        super().__init__("core.mechanic.great_person_explorer", value=value)
