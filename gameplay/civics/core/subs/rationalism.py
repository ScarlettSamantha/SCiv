from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Rationalism(BaseCoreSubtree):
    key = "core.culture.subtrees.rationalism"
    name = t_("content.culture.subtrees.core.rationalism.name")
    description = t_("content.culture.subtrees.core.rationalism.description")
    order = 6

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.education_reform import EducationReform
        from gameplay.civics.core.evidence_based_policy import EvidenceBasedPolicy
        from gameplay.civics.core.philosophical_discourse import PhilosophicalDiscourse
        from gameplay.civics.core.reason_and_logic import ReasonAndLogic
        from gameplay.civics.core.scientific_inquiry import ScientificInquiry
        from gameplay.civics.core.secular_governance import SecularGovernance

        reason_and_logic = ReasonAndLogic
        reason_and_logic.unlocks = [ScientificInquiry, SecularGovernance]
        reason_and_logic.tier = 0
        cls.add_civic(reason_and_logic)

        scientific_inquiry = ScientificInquiry
        scientific_inquiry.add_requirement(CivicCondition(reason_and_logic))
        scientific_inquiry.tier = 1
        scientific_inquiry.unlocks = [EducationReform]
        cls.add_civic(scientific_inquiry)

        secular_governance = SecularGovernance
        secular_governance.add_requirement(CivicCondition(reason_and_logic))
        secular_governance.tier = 1
        cls.add_civic(secular_governance)

        education_reform = EducationReform
        education_reform.add_requirement(CivicCondition(scientific_inquiry))
        education_reform.tier = 2
        education_reform.unlocks = [EvidenceBasedPolicy]
        cls.add_civic(education_reform)

        evidence_based_policy = EvidenceBasedPolicy
        evidence_based_policy.add_requirement(CivicCondition(education_reform))
        evidence_based_policy.tier = 3
        cls.add_civic(evidence_based_policy)

        philosophical_discourse = PhilosophicalDiscourse
        philosophical_discourse.add_requirement(CivicCondition(evidence_based_policy))
        philosophical_discourse.tier = 4
        cls.add_civic(philosophical_discourse)

        return [
            reason_and_logic,
            scientific_inquiry,
            secular_governance,
            education_reform,
            evidence_based_policy,
            philosophical_discourse,
        ]
