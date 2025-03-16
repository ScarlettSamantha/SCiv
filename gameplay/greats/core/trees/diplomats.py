from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class DiplomatsGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.diplomacy",
            name=_t("content.greats.core.trees.diplomacy.name"),
            description=_t("content.greats.core.trees.diplomacy.description"),
        )
        self.load_folder = "core/diplomats/"

