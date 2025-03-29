from typing import Any

from gameplay.culture import CultureTree
from managers.i18n import t_
from system.pyload import PyLoad


class CoreCultureTree(CultureTree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.tree",
            name=t_("content.culture.tree.core.name"),
            description=t_("content.culture.tree.core.name"),
        )

    def _load_subclasses(self):
        return PyLoad.load_classes("openciv/gameplay/cultures/core/subs", lambda x: not x.startswith("_"))

    def register_subtrees(self):
        # We just load all the classes in the subs directory and add them as subtrees
        classes = self._load_subclasses()
        for _, subtree in classes.items():
            self.add_subtree(subtree())
