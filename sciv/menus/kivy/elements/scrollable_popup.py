from typing import Any, Callable, Dict, List, Optional, Tuple

from kivy.graphics import Color, Rectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout  # type: ignore
from kivy.uix.button import Button  # type: ignore
from kivy.uix.gridlayout import GridLayout  # type: ignore
from kivy.uix.popup import Popup  # type: ignore
from kivy.uix.scrollview import ScrollView  # type: ignore
from kivy.uix.widget import Widget  # type: ignore
from menus.kivy.elements.button_value import ButtonValue  # type: ignore


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
    ) -> None:
        super().__init__(**kwargs)  # type: ignore

        self.title = title
        self.size_hint = popup_size

        root = BoxLayout(
            orientation="vertical",
            padding=(dp(24), dp(20)),
            spacing=dp(12),
        )

        with root.canvas.before:  # type: ignore
            Color(0.08, 0.08, 0.12, 0.95)
            bg_rect = Rectangle(size=root.size, pos=root.pos)  # type: ignore

        def _update_bg(instance: Widget, _value: Any) -> None:
            bg_rect.size = instance.size  # type: ignore
            bg_rect.pos = instance.pos  # type: ignore

        root.bind(size=_update_bg, pos=_update_bg)  # type: ignore

        scroll_view = ScrollView(
            size_hint=(1.0, 1.0),
            do_scroll_x=False,
            bar_width=dp(8),
        )

        list_layout = GridLayout(
            cols=cols,
            size_hint_y=None,
            spacing=(dp(8), dp(8)),
            padding=(dp(8), dp(8)),
            row_force_default=True,
            row_default_height=dp(button_height),
        )
        list_layout.bind(minimum_height=list_layout.setter("height"))  # type: ignore

        ref_bound_button = Button if isinstance(items, list) else ButtonValue
        has_values = isinstance(items, dict)

        if not has_values:
            for text in items:  # type: ignore[assignment]
                btn = ref_bound_button(
                    text=text,
                    size_hint_y=None,
                    height=dp(button_height),
                    background_normal="",
                    background_down="",
                    background_color=(0.18, 0.2, 0.26, 1.0),
                    color=(1.0, 1.0, 1.0, 1.0),
                )
                btn.bind(
                    on_release=lambda _btn, txt=text: self.select_item(txt, on_select)  # type: ignore
                )
                list_layout.add_widget(btn)
        else:
            for text, value in items.items():  # type: ignore[union-attr]
                btn = ref_bound_button(
                    text=text,
                    value=value,
                    size_hint_y=None,
                    height=dp(button_height),
                    background_normal="",
                    background_down="",
                    background_color=(0.18, 0.2, 0.26, 1.0),
                    color=(1.0, 1.0, 1.0, 1.0),
                )
                btn.bind(
                    on_release=lambda _btn, txt=text, val=value: self.select_item(  # type: ignore
                        txt,
                        on_select,
                        val,
                    )
                )
                list_layout.add_widget(btn)

        scroll_view.add_widget(list_layout)  # type: ignore

        button_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(button_height + 8),
            spacing=dp(10),
        )

        button_row.add_widget(Widget(size_hint_x=1.0))

        close_button = Button(
            text="Close",
            size_hint=(None, None),
            width=dp(160),
            height=dp(button_height),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
        )
        close_button.bind(on_release=self.dismiss)  # type: ignore

        button_row.add_widget(close_button)

        root.add_widget(scroll_view)
        root.add_widget(button_row)

        self.content = root

    def select_item(
        self,
        item: str,
        on_select: Callable[[str, Optional[Any]], None],
        value: Optional[Any] = None,
    ) -> None:
        if value is None:
            on_select(item, None)
        else:
            on_select(item, value)
        self.dismiss()  # type: ignore

    def add_child(self, child: Widget) -> None:
        self.content.add_widget(child)

    def remove_child(self, child: Widget) -> None:
        self.content.remove_widget(child)
