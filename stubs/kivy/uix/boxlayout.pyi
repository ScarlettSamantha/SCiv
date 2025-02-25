from typing import Optional, Tuple

from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, ReferenceListProperty, StringProperty

class BoxLayout(Layout):
    minimum_width: NumericProperty
    minimum_height: NumericProperty
    minimum_size: ReferenceListProperty[Tuple[int, int]]
    orientation: StringProperty
    spacing: NumericProperty

    def __init__(self, orientation: Optional[str] = "horizontal", spacing: Optional[int] = 10) -> None: ...
    def add_widget(self, widget: Layout) -> None: ...
    def remove_widget(self, widget: Layout) -> None: ...
    def bind(self, **kwargs) -> None: ...
    def fbind(self, **kwargs) -> None: ...
