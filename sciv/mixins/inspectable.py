from typing import Any, Dict, Tuple


class Inspectable:
    def __init__(self):
        self.hidden_in_tree: bool = False

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return {}, {}

    def is_visible(self) -> bool:
        return not self.hidden_in_tree
