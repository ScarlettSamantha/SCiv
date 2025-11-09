from typing import Any, Callable, Dict, List, Optional, Tuple

from kivy.uix.widget import Widget
from kivy.properties import ReferenceListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from menus.kivy.elements.button_value import ButtonValue


class ScrollablePopup(Popup):
    def __init__(
        self,
        title: str,
        items: List[str] | Dict[str, Any],
        on_select: Callable[[str, Optional[Any]], None],
        cols: int = 3,
        button_height: int = 50,
        popup_size: Tuple[float, float] = (0.6, 0.6),
        **kwargs: Any,
    ):
        super().__init__(**kwargs)  # type: ignore
        self.title: str = title
        self.size_hint: ReferenceListProperty[Tuple[float, float]] | Tuple[float, float] = popup_size

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Scrollable list container (constrained height)
        scroll_view = ScrollView(height=400, smooth_scroll_end=10, pos=(500, 200))
        scroll_view._update_effect_y_bounds()  # type: ignore # Limited height for scrolling

        list_layout = GridLayout(cols=cols, size_hint_y=None, spacing=5, padding=[5, 5], height=100)
        list_layout.bind(minimum_height=list_layout.setter("height"))  # type: ignore # Adjust dynamically

        ref_bound_button = Button if isinstance(items, list) else ButtonValue
        has_values = isinstance(items, dict)

        # Populate with options
        if not has_values:
            for item in items:
                btn = ref_bound_button(text=item, size_hint_y=None, height=button_height)
                btn.bind(on_release=lambda btn: self.select_item(btn.text, on_select))  # type: ignore
                list_layout.add_widget(btn)
        else:
            for text, value in items.items():
                btn = ref_bound_button(text=text, value=value, size_hint_y=None, height=button_height)
                btn.bind(on_release=lambda btn: self.select_item(btn.text, on_select, btn.value))  # type: ignore
                list_layout.add_widget(btn)

        scroll_view.add_widget(list_layout)  # type: ignore

        # Close button with padding
        close_button = Button(text="Close", size_hint=(1, None), height=button_height)
        close_button.bind(on_release=self.dismiss)  # type: ignore

        layout.add_widget(scroll_view)
        layout.add_widget(close_button)

        self.content = layout

    def select_item(self, item: str, on_select: Callable[[str, Optional[Any]], None], value: Optional[Any] = None):
        if value is None:
            on_select(item, None)
        else:
            on_select(item, value)
        self.dismiss()  # type: ignore

    def add_child(self, child: Widget):
        self.content.add_widget(child)

    def remove_child(self, child: Widget):
        self.content.remove_widget(child)
