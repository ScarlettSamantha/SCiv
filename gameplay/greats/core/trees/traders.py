from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class TradersGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.traders",
            name=_t("content.greats.core.trees.traders.name"),
            description=_t("content.greats.core.trees.traders.description"),
        )
        self.load_folder = "core/traders/"
