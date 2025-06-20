from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class DiplomatsGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.diplomacy",
            name=t_("content.greats.core.trees.diplomacy.name"),
            description=t_("content.greats.core.trees.diplomacy.description"),
        )
        self.load_folder = "core/diplomats/"
