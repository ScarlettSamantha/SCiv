from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class HolyGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.holy",
            name=_t("content.greats.core.trees.holy.name"),
            description=_t("content.greats.core.trees.holy.description"),
        )
        self.load_folder = "core/holy/"

