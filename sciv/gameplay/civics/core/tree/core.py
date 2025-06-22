from typing import Any, Dict, Type

from gameplay.civic import CivicSubtree, CivicTree
from managers.i18n import t_
from system.pyload import PyLoad


class CoreCivicTree(CivicTree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.tree",
            name=t_("content.culture.tree.core.name"),
            description=t_("content.culture.tree.core.name"),
        )

    def _load_subclasses(self) -> Dict[str, Type[CivicSubtree]]:
        return PyLoad.load_classes(
            "gameplay/civics/core/subs", lambda x: not x.startswith("_"), package="gameplay.civics.core.subs"
        )

    def register_subtrees(self):
        # We just load all the classes in the subs directory and add them as subtrees
        classes = self._load_subclasses()
        self.subtrees = []
        for _, subtree in classes.items():
            self.add_subtree(subtree)
