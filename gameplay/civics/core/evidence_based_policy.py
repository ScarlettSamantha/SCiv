from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EvidenceBasedPolicy(Civic):
    key = "core.culture.civics.evidence_based_policy"
    name = t_("content.culture.civics.core.evidence_based_policy.name")
    description = t_("content.culture.civics.core.evidence_based_policy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
