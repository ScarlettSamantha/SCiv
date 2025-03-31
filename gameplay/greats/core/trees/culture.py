from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class CultureGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.culture",
            name=t_("content.greats.core.trees.culture.name"),
            description=t_("content.greats.core.trees.culture.description"),
        )
        self.load_folder = "core/artists/"
