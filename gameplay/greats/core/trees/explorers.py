from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class ExplorersGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.explorers",
            name=t_("content.greats.core.trees.explorers.name"),
            description=t_("content.greats.core.trees.explorers.description"),
        )
        self.load_folder = "core/explorers/"
