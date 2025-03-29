from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class HolyGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.holy",
            name=t_("content.greats.core.trees.holy.name"),
            description=t_("content.greats.core.trees.holy.description"),
        )
        self.load_folder = "core/holy/"
