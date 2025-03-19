from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class ExplorersGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.explorers",
            name=_t("content.greats.core.trees.explorers.name"),
            description=_t("content.greats.core.trees.explorers.description"),
        )
        self.load_folder = "core/explorers/"
