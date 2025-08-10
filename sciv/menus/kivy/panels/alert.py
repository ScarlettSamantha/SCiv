from typing import Any, Callable, Optional

from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from menus.kivy.elements.modal import ModalPanel


class AlertPanel(ModalPanel):
    def __init__(
        self,
        title: str = "Alert",
        message: str = "",
        icon_source: str | Image | None = None,
        ok_text: str = "OK",
        on_ok: Optional[Callable[[], None]] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            padding=[dp(16), dp(16), dp(16), dp(16)],  # type: ignore
        )

        if icon_source:
            icon_size = dp(64)
            if isinstance(icon_source, Image):
                from helpers.images import clone_image_widget

                self._icon = clone_image_widget(icon_source)
                self._icon.size_hint = (None, None)
                self._icon.size = (icon_size, icon_size)
            else:
                path_icon = icon_source

                self._icon = Image(
                    source=path_icon,
                    size_hint=(None, None),
                    size=(icon_size, icon_size),
                    keep_ratio=True,
                    allow_stretch=False,
                    opacity=1.0,
                )

            icon_anchor = AnchorLayout(
                anchor_x="left",
                anchor_y="top",
                size_hint=(None, 1),
                width=dp(112),
            )
            icon_anchor.add_widget(self._icon)
            root.add_widget(icon_anchor)

        right = BoxLayout(orientation="vertical", spacing=dp(8), size_hint=(1, 1))

        self._title = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            size_hint=(1, None),
            height=dp(40),
            halign="left",
            valign="middle",
            color=(1, 1, 1, 1),
            font_size=dp(32),
        )
        self._title.bind(size=lambda inst, s: setattr(inst, "text_size", s))  # type: ignore
        right.add_widget(self._title)

        self._label = Label(
            text=message,
            halign="left",
            valign="top",
            size_hint=(1, None),
            color=(1, 1, 1, 1),
            markup=True,
        )
        self._label.bind(size=lambda inst, s: setattr(inst, "text_size", (s[0], None)))  # type: ignore
        self._label.bind(texture_size=lambda inst, s: setattr(inst, "height", s[1]))  # type: ignore

        scroller = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(6),
            bar_color=(1, 1, 1, 0.35),
            bar_inactive_color=(1, 1, 1, 0.15),
        )
        scroller.add_widget(self._label)
        right.add_widget(scroller)

        root.add_widget(right)
        self.set_content(root)

        self.clear_action_buttons()
        self.add_action_button(ok_text, on_press=self._on_ok if on_ok else self.dismiss)
        self._on_ok_cb = on_ok

    def clear_action_buttons(self) -> None:
        self._buttons_box.clear_widgets()
        self._buttons_box.add_widget(self._close_btn)
        self._close_btn.size_hint = (None, None)  # type: ignore
        self._close_btn.width = dp(120)

    def set_icon(self, source: str) -> None:
        if hasattr(self, "_icon"):
            self._icon.source = source

    def set_text(self, value: str) -> None:
        self._label.text = value

    def get_text(self) -> str:
        return self._label.text

    def register_on_click(self) -> None:
        self.on_click = self.open

    def _on_ok(self) -> None:
        if self._on_ok_cb:
            self._on_ok_cb()
        self.dismiss()
