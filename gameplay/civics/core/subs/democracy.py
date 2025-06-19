from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Democracy(BaseCoreSubtree):
    key = "core.culture.subtrees.democracy"
    name = t_("content.culture.subtrees.core.democracy.name")
    description = t_("content.culture.subtrees.core.democracy.description")
    order = 7

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.electoral_process import ElectoralProcess
        from gameplay.civics.core.human_rights import HumanRights
        from gameplay.civics.core.participatory_governance import ParticipatoryGovernance
        from gameplay.civics.core.rule_of_law import RuleOfLaw
        from gameplay.civics.core.separation_of_powers import SeparationOfPowers
        from gameplay.civics.core.transparent_government import TransparentGovernment

        electoral_process = ElectoralProcess
        electoral_process.tier = 0
        electoral_process.unlocks = [RuleOfLaw]
        cls.add_civic(electoral_process)

        rule_of_law = RuleOfLaw
        rule_of_law.set_requirements([CivicCondition(electoral_process)])
        rule_of_law.tier = 1
        rule_of_law.unlocks = [SeparationOfPowers, ParticipatoryGovernance]
        cls.add_civic(rule_of_law)

        separation_of_powers = SeparationOfPowers
        separation_of_powers.set_requirements([CivicCondition(rule_of_law)])
        separation_of_powers.tier = 2
        separation_of_powers.unlocks = [HumanRights]
        cls.add_civic(separation_of_powers)

        human_rights = HumanRights
        human_rights.set_requirements([CivicCondition(separation_of_powers)])
        human_rights.tier = 3
        human_rights.unlocks = [ParticipatoryGovernance, TransparentGovernment]
        cls.add_civic(human_rights)

        participatory_governance = ParticipatoryGovernance
        participatory_governance.set_requirements([CivicCondition(rule_of_law), CivicCondition(human_rights)])
        participatory_governance.unlocks = [TransparentGovernment]
        participatory_governance.tier = 4
        cls.add_civic(participatory_governance)

        transparent_government = TransparentGovernment
        transparent_government.set_requirements([CivicCondition(human_rights)])
        transparent_government.tier = 4
        cls.add_civic(transparent_government)

        return [
            electoral_process,
            rule_of_law,
            separation_of_powers,
            human_rights,
            participatory_governance,
            transparent_government,
        ]
