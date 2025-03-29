from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import t_


class MilitaryGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.military",
            name=t_("content.greats.core.trees.military.name"),
            description=t_("content.greats.core.trees.military.description"),
        )
        self.load_folder = "core/military/"
