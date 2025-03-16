from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class MilitaryGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.military",
            name=_t("content.greats.core.trees.military.name"),
            description=_t("content.greats.core.trees.military.description"),
        )
        self.load_folder = "core/military/"

