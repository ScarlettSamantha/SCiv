from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class CultureGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.culture",
            name=_t("content.greats.core.trees.culture.name"),
            description=_t("content.greats.core.trees.culture.description"),
        )
        self.load_folder = "core/artists/"


