from gameplay.cultures.core.subs._base import BaseCoreSubtree
from managers.i18n import _t


class Federalism(BaseCoreSubtree):
    def __init__(self):
        super().__init__(
            key="core.culture.subtrees.federalism",
            name=_t("content.culture.subtrees.core.federalism.name"),
            description=_t("content.culture.subtrees.core.federalism.description"),
        )
