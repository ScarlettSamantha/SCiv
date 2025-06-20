from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class ScientistsGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.scientists",
            name=t_("content.greats.core.trees.scientists.name"),
            description=t_("content.greats.core.trees.scientists.description"),
        )
        self.load_folder = "core/scientists/"
