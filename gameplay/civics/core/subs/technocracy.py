from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Technocracy(BaseCoreSubtree):
    key = "core.culture.subtrees.technocracy"
    name = t_("content.culture.subtrees.core.technocracy.name")
    description = t_("content.culture.subtrees.core.technocracy.description")
    order = 12

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.data_driven_policy import DataDrivenPolicy
        from gameplay.civics.core.efficient_administration import EfficientAdministration
        from gameplay.civics.core.expert_governance import ExpertGovernance
        from gameplay.civics.core.innovation_focus import InnovationFocus
        from gameplay.civics.core.meritocracy import Meritocracy
        from gameplay.civics.core.scientific_management import ScientificManagement

        expert_governance = ExpertGovernance
        expert_governance.tier = 0
        expert_governance.unlocks = [ScientificManagement, InnovationFocus]
        cls.add_civic(expert_governance)

        scientific_management = ScientificManagement
        scientific_management.add_requirement(CivicCondition(expert_governance))
        scientific_management.tier = 1
        scientific_management.unlocks = [DataDrivenPolicy]
        cls.add_civic(scientific_management)

        innovation_focus = InnovationFocus
        innovation_focus.add_requirement(CivicCondition(expert_governance))
        innovation_focus.tier = 1
        innovation_focus.unlocks = [DataDrivenPolicy]
        cls.add_civic(innovation_focus)

        data_driven_policy = DataDrivenPolicy
        data_driven_policy.add_requirement(CivicCondition(scientific_management))
        data_driven_policy.add_requirement(CivicCondition(innovation_focus))
        data_driven_policy.tier = 2
        data_driven_policy.unlocks = [EfficientAdministration]
        cls.add_civic(data_driven_policy)

        efficient_administration = EfficientAdministration
        efficient_administration.add_requirement(CivicCondition(data_driven_policy))
        efficient_administration.tier = 3
        efficient_administration.unlocks = [Meritocracy]
        cls.add_civic(efficient_administration)

        meritocracy = Meritocracy
        meritocracy.add_requirement(CivicCondition(efficient_administration))
        meritocracy.tier = 4
        cls.add_civic(meritocracy)

        return [
            expert_governance,
            scientific_management,
            innovation_focus,
            data_driven_policy,
            efficient_administration,
            meritocracy,
        ]
