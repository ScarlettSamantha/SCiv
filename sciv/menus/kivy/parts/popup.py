# menus/kivy/parts/popup.py

import math
from typing import Any, Callable, List, Tuple

from kivy.metrics import dp  # type: ignore
from kivy.properties import ListProperty, ObjectProperty  # type: ignore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from menus.kivy.elements.select import SelectButton
from managers.i18n import T_TranslationOrStr, t_


class BasePopup(Popup):
    callback: ObjectProperty = ObjectProperty(None)  # type: ignore
    on_close: ObjectProperty = ObjectProperty(None)  # type: ignore

    def __init__(
        self,
        callback: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: T_TranslationOrStr = t_("ui.player_ui.generics.popup"),
        size_hint: Tuple[float, float] = (0.8, 0.6),
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(title=str(title), **kwargs)  # type: ignore
        self.callback: Callable[..., Any] | None = callback
        self.on_close: Callable[..., Any] | None = on_close  # type: ignore
        self.bind(on_dismiss=self._handle_close)  # type: ignore
        self.size_hint = size_hint
        self.is_open: bool = False
        self.auto_dismiss = False

    def open(self, *args: Any, **kwargs: Any):
        self.is_open = True
        return super().open(*args, **kwargs)

    def done(self, value: Any = None):
        if self.callback:
            self.callback(value)
        self.is_open = False
        self.dismiss()  # type:ignore

    def _handle_close(self, instance: Popup):
        if self.on_close:
            self.on_close()


class DoubleSpinnerPopup(BasePopup):
    items1: ListProperty = ListProperty([])  # type: ignore
    items2: ListProperty = ListProperty([])  # type: ignore
    on_change1: ObjectProperty = ObjectProperty(None)  # type: ignore
    on_change2: ObjectProperty = ObjectProperty(None)  # type: ignore

    def __init__(
        self,
        items1: List[Tuple[str, Any]],
        items2: List[Tuple[str, Any]],
        callback: Callable[..., Any] | None = None,
        on_change1: Callable[..., Any] | None = None,
        on_change2: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: T_TranslationOrStr = "Select Items",
        ok_text: T_TranslationOrStr = t_("ui.player_ui.generics.ok"),
        cancel_text: T_TranslationOrStr = t_("ui.player_ui.generics.cancel"),
        size_hint: Tuple[float, float] = (0.8, 0.5),
        **kwargs: Any,
    ):
        super().__init__(callback=callback, on_close=on_close, title=title, size_hint=size_hint, **kwargs)
        self.items1 = items1
        self.items2 = items2
        self.on_change1: Callable[..., Any] | None = on_change1
        self.on_change2: Callable[..., Any] | None = on_change2

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        spinner_layout = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint=(1, None), height=dp(44))

        self.spinner1 = SelectButton(items=self.items1, on_select=self._on_select1, size_hint=(0.5, None))
        self.spinner2 = SelectButton(items=self.items2, on_select=self._on_select2, size_hint=(0.5, None))
        spinner_layout.add_widget(self.spinner1)
        spinner_layout.add_widget(self.spinner2)

        content.add_widget(spinner_layout)

        btn_layout = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        self.ok_button = Button(text=str(ok_text))
        self.ok_button.bind(on_release=self.on_ok)
        self.cancel_button = Button(text=str(cancel_text))
        self.cancel_button.bind(on_release=self.dismiss)  # type:ignore
        btn_layout.add_widget(self.ok_button)
        btn_layout.add_widget(self.cancel_button)
        content.add_widget(btn_layout)

        self.content: BoxLayout = content

    def _on_select1(self, value: Any) -> None:
        if self.on_change1:
            self.on_change1(value)

    def _on_select2(self, value: Any) -> None:
        if self.on_change2:
            self.on_change2(value)

    @property
    def selected1(self) -> Any:
        return self.spinner1.selected_value

    @property
    def selected2(self) -> Any:
        return self.spinner2.selected_value

    def on_ok(self, instance: Button) -> None:
        self.done((self.selected1, self.selected2))

    def get_selected(self) -> Tuple[Any, Any]:
        return (self.selected1, self.selected2)

    def set_items1(self, items: List[Tuple[str, Any]], keep_selection: bool = False) -> None:
        self.items1 = items
        self.spinner1.set_items(items, keep_selection=keep_selection)

    def set_items2(self, items: List[Tuple[str, Any]], keep_selection: bool = False) -> None:
        self.items2 = items
        self.spinner2.set_items(items, keep_selection=keep_selection)


class MenuPopup(BasePopup):
    items = ListProperty([])  # type:ignore
    on_change = ObjectProperty(None)  # type:ignore

    def __init__(
        self,
        items: List[Tuple[str, Any]],
        callback: Callable[..., Any] | None = None,
        on_change: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: T_TranslationOrStr = t_("ui.player_ui.generics.select_item"),
        ok_text: T_TranslationOrStr = t_("ui.player_ui.generics.ok"),
        cancel_text: T_TranslationOrStr = t_("ui.player_ui.generics.cancel"),
        size_hint: Tuple[float, float] = (0.8, 0.4),
        **kwargs: Any,
    ):
        super().__init__(callback=callback, on_close=on_close, size_hint=size_hint, title=title, **kwargs)
        self.items: List[Tuple[str, Any]] = items
        self.on_change: Callable[..., Any] | None = on_change

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        self.selector = SelectButton(items=self.items, on_select=self._handle_change, size_hint=(1, None))
        content.add_widget(self.selector)

        btn_layout = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        self.ok_button = Button(text=str(ok_text))
        self.ok_button.bind(on_release=self.on_ok)
        self.cancel_button = Button(text=str(cancel_text))
        self.cancel_button.bind(on_release=self.dismiss)  # type: ignore
        btn_layout.add_widget(self.ok_button)
        btn_layout.add_widget(self.cancel_button)
        content.add_widget(btn_layout)

        self.content = content

    @property
    def selected(self) -> Any:
        return self.selector.selected_value

    def _handle_change(self, value: Any):
        if self.on_change:
            self.on_change(value)

    def on_ok(self, instance: Button) -> None:
        self.done(self.selected)

    def _refresh_items(self, keep_selection: bool = False):
        self.selector.set_items(self.items, keep_selection=keep_selection)

    def add_item(self, item: Tuple[str, Any]):
        if item not in self.items:
            self.items.append(item)
            self._refresh_items(keep_selection=True)

    def insert_item(self, index: int, item: Tuple[str, Any]):
        self.items.insert(index, item)
        self._refresh_items(keep_selection=True)

    def remove_item(self, item: Tuple[str, Any]):
        if item in self.items:
            self.items.remove(item)
            self._refresh_items(keep_selection=False)

    def delete_item_at(self, index: int):
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._refresh_items(keep_selection=False)

    def get_selected(self):
        return self.selected


class GridPopup(BasePopup):
    def __init__(
        self,
        rows: int = 2,
        cols: int = 2,
        callback: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: str = "Grid Popup",
        size_hint: Tuple[float, float] = (0.8, 0.6),
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(callback=callback, size_hint=size_hint, on_close=on_close, title=title, **kwargs)

        container = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        self.grid = GridLayout(rows=rows, cols=cols, spacing=dp(5), size_hint=(1, 1))
        container.add_widget(self.grid)

        btn_layout = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        confirm_btn = Button(text=str(t_("ui.player_ui.generics.confirm")))
        confirm_btn.bind(on_release=lambda *args: self.done(self._collect_values()))
        cancel_btn = Button(text=str(t_("ui.player_ui.generics.cancel")))
        cancel_btn.bind(on_release=self.dismiss)  # type: ignore
        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)
        container.add_widget(btn_layout)

        self.content: BoxLayout = container

    def add_widget_item(self, widget: Widget):
        self.grid.add_widget(widget)

    def remove_widget_item(self, widget: Widget):
        if widget in self.grid.children:
            self.grid.remove_widget(widget)

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self.grid.clear_widgets(children=children)

    def _collect_values(self) -> List[Any]:
        collected: List[Any] = []
        for w in reversed(self.grid.children):
            if hasattr(w, "text"):
                collected.append(w.text)  # type: ignore
        return collected


class ButtonGridPopup(BasePopup):
    def __init__(
        self,
        items: List[Tuple[str, Any]],
        rows: int = 0,
        cols: int = 0,
        callback: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: str = "Select Item",
        size_hint: Tuple[float, float] = (0.8, 0.6),
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(callback=callback, on_close=on_close, title=title, size_hint=size_hint, **kwargs)
        size = len(items)
        if rows <= 0 or cols <= 0:
            cols = int(math.ceil(math.sqrt(size))) if size else 1
            rows = int(math.ceil(size / cols)) if size else 1

        container = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        self.grid = GridLayout(rows=rows, cols=cols, spacing=dp(5), size_hint=(1, 1))
        for label, value in items:
            btn = self.create_button(label, value)
            self.grid.add_widget(btn)
        container.add_widget(self.grid)

        btn_layout = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        cancel_btn = Button(text=str(t_("ui.player_ui.generics.cancel")))
        cancel_btn.bind(on_release=self.dismiss)  # type: ignore
        btn_layout.add_widget(cancel_btn)
        container.add_widget(btn_layout)

        self.content: BoxLayout = container

    def create_button(self, text: str, value: Any) -> Button:
        btn = Button(text=text, size_hint_y=None, height=dp(44))
        setattr(btn, "value", value)
        btn.bind(on_release=self._on_button_click)
        return btn

    def _on_button_click(self, instance: Button):
        value = getattr(instance, "value", instance.text)
        self.done(value)
