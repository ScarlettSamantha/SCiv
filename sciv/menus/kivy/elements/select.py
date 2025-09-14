from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple

from kivy.clock import Clock  # type: ignore
from kivy.core.window import Window  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.widget import Widget

from helpers.cache import Cache


WindowSizeProvider = Callable[[], Tuple[int, int]]


class SelectDropdown(ModalView):
    def __init__(
        self,
        *,
        anchor: Widget,
        labels: List[str],
        on_pick: Callable[[int], None],
        row_height: float = 36,
        max_height: float = 260,
        selected_index: int = -1,
        match_anchor_width: bool = True,
        min_width: float = 240,
        window_size_provider: Optional[WindowSizeProvider] = None,
        keyboard_nav: bool = True,
        dim: float = 0.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.background = ""
        self.background_color = (0, 0, 0, max(0.0, min(dim, 1.0)))
        self.auto_dismiss = True

        self._anchor = anchor
        self._labels = labels
        self._on_pick = on_pick
        self._row_h = dp(row_height)
        self._max_h = dp(max_height)
        self._sel = max(-1, min(selected_index, len(labels) - 1))
        self._keyboard_nav = keyboard_nav
        self._window_size_provider = window_size_provider or (lambda: tuple(Window.size))  # type: ignore

        self._root = FloatLayout(size_hint=(1, 1))
        self.add_widget(self._root)

        anchor_w = getattr(self._anchor, "width", 0)
        panel_w = max(min_width, anchor_w) if match_anchor_width else max(dp(min_width), dp(240))
        panel_h = min(self._max_h, self._row_h * max(1, len(self._labels)) + dp(12))
        self._panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=panel_w,
            height=panel_h,
            padding=dp(6),
            spacing=dp(6),
        )
        self._root.add_widget(self._panel)

        self._rv = RecycleView(size_hint=(1, 1))
        rbl = RecycleBoxLayout(
            orientation="vertical",
            default_size=(None, self._row_h),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(2),
        )
        rbl.bind(minimum_height=rbl.setter("height"))
        self._rv.add_widget(rbl)  # type: ignore
        self._rv.viewclass = "Button"

        def row(i: int, txt: str) -> Dict[str, Any]:
            return {
                "text": txt,
                "state": "down" if i == self._sel and self._sel >= 0 else "normal",
                "on_release": partial(self._pick_and_close, i),
                "size_hint_y": None,
                "height": self._row_h,
            }

        self._rv.data = [row(i, lbl) for i, lbl in enumerate(self._labels)]
        self._panel.add_widget(self._rv)

        Clock.schedule_once(lambda *_: self._position_panel(), 0)  # type: ignore

        if self._keyboard_nav:
            from kivy.core.window import Window as _W

            self.bind(on_open=lambda *_: _W.bind(on_key_down=self._on_key_down))  # type: ignore
            self.bind(on_dismiss=lambda *_: _W.unbind(on_key_down=self._on_key_down))  # type: ignore

    def _position_panel(self) -> None:
        ax, ay = self._anchor.to_window(self._anchor.x, self._anchor.y)  # bottom-left
        aw, ah = self._anchor.width, self._anchor.height  # type: ignore
        win_w, win_h = self._window_size_provider()  # type: ignore

        below_y = ay - self._panel.height
        above_y = ay + ah
        py = below_y if below_y >= 0 else min(above_y, win_h - self._panel.height)  # type: ignore
        px = min(max(ax, 0), max(0, win_w - self._panel.width))  # type: ignore
        rx, ry = self._root.to_widget(px, py)
        self._panel.pos = (rx, ry)  # type: ignore

    def _apply_sel_visual(self) -> None:
        for i, d in enumerate(self._rv.data):  # type: ignore
            d["state"] = "down" if i == self._sel else "normal"
        self._rv.refresh_from_data()  # type: ignore

    def _move_sel(self, delta: int) -> None:
        if not self._labels:
            return
        if self._sel < 0:
            self._sel = 0
        else:
            self._sel = (self._sel + delta) % len(self._labels)
        self._apply_sel_visual()
        target_y = self._sel * (self._row_h + dp(2))
        view_h = float(self._panel.height)
        total_h = max(self._row_h * len(self._labels) + dp(2) * (len(self._labels) - 1), 1)
        from_top = min(max(target_y - view_h * 0.4, 0), max(total_h - view_h, 0))
        self._rv.scroll_y = 1.0 - (from_top / max(total_h - view_h, 1))

    def _on_key_down(self, _win, keycode, scancode, codepoint, modifiers):  # type: ignore
        name = keycode[1] if isinstance(keycode, tuple) else str(keycode)  # type: ignore
        if name in ("up", "k"):
            self._move_sel(-1)
            return True
        if name in ("down", "j"):
            self._move_sel(1)
            return True
        if name in ("enter", "kpenter"):
            if 0 <= self._sel < len(self._labels):
                self._pick_and_close(self._sel)
            return True
        if name in ("escape",):
            self.dismiss()
            return True
        return False

    def _pick_and_close(self, index: int, *args: Any):
        try:
            self._on_pick(index)
        finally:
            self.dismiss()


class SelectButton(Button):
    dropdown_cls: Callable[..., SelectDropdown] = SelectDropdown

    def __init__(
        self,
        *,
        items: Optional[List[Tuple[str, Any]]] = None,
        on_select: Optional[Callable[[Any], None]] = None,
        text_when_empty: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(44)

        self._items: List[Tuple[str, Any]] = list(items or [])
        self._on_select_cb = on_select
        self._selected_index: int = 0 if self._items else -1
        self.text = self._items[0][0] if self._items else text_when_empty

        self.bind(on_release=self._open_dropdown)  # type: ignore

    @property
    def values(self) -> List[Tuple[str, Any]]:
        return list(self._items)

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_value(self) -> Any:
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index][1]
        return None

    def set_items(self, items: List[Tuple[str, Any]], keep_selection: bool = False) -> None:
        prev_label = self.text
        self._items = list(items or [])
        if not self._items:
            self._selected_index = -1
            self.text = ""
            return
        if keep_selection and prev_label:
            for i, (lbl, _v) in enumerate(self._items):
                if lbl == prev_label:
                    self._selected_index = i
                    self.text = lbl
                    return
        self._selected_index = 0
        self.text = self._items[0][0]

    def set_selected_by_value(self, value: Any) -> bool:
        for i, (_lbl, v) in enumerate(self._items):
            if v == value:
                self._selected_index = i
                self.text = self._items[i][0]
                return True
        return False

    def set_selected_by_label(self, label: str) -> bool:
        for i, (lbl, _v) in enumerate(iterable=self._items):
            if lbl == label:
                self._selected_index = i
                self.text = label
                return True
        return False

    def _open_dropdown(self, *_):
        if not self._items:
            return

        win_x, win_y = Cache.get_showbase_instance().win.size

        labels = [lbl for lbl, _ in self._items]
        panel = self.dropdown_cls(
            anchor=self,
            labels=labels,
            on_pick=self._on_pick,
            row_height=dp(36),
            max_height=dp(260),
            selected_index=self._selected_index,
            window_size_provider=lambda: (win_x, win_y),  # type: ignore
        )
        panel.open()

    def _on_pick(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._selected_index = index
            self.text = self._items[index][0]
            if self._on_select_cb:
                self._on_select_cb(self._items[index][1])


__all__ = ["SelectDropdown", "SelectButton"]
