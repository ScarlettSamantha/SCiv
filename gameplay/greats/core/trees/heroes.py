from gameplay.greats.core.trees._base import BaseCoreGreatsTree
from managers.i18n import _t


class HeroesGreatsTree(BaseCoreGreatsTree):
    def __init__(self):
        super().__init__(
            key="core.greats.tree.heroes",
            name=_t("content.greats.core.trees.heroes.name"),
            description=_t("content.greats.core.trees.heroes.description"),
        )
        self.load_folder = "core/heroes/"
