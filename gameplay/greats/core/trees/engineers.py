from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class EngineersGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.engineers",
            name=_t("content.greats.core.trees.engineers.name"),
            description=_t("content.greats.core.trees.engineers.description"),
        )
        self.load_folder = "core/engineers/"
