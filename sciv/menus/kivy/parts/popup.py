import math
from typing import Any, Callable, Dict, List, Tuple

from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget


class BasePopup(Popup):
    callback: ObjectProperty = ObjectProperty(None)  # type:ignore
    on_close: ObjectProperty = ObjectProperty(None)  # type:ignore

    def __init__(
        self,
        callback: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: str = "Popup",
        size_hint: Tuple[float, float] = (0.8, 0.6),
        *args: Any,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(title=title, **kwargs)  # type:ignore
        self.callback: Callable[..., Any] | None = callback
        self.on_close: Callable[..., Any] | None = on_close
        self.bind(on_dismiss=self._handle_close)  # type:ignore
        self.size_hint = size_hint

    def done(self, value: Any = None):
        if self.callback:
            self.callback(value)
        self.dismiss()  # type:ignore

    def _handle_close(self, instance: Button):
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
        title: str = "Select Items",
        ok_text: str = "OK",
        cancel_text: str = "Cancel",
        size_hint: Tuple[float, float] = (0.8, 0.5),
        **kwargs: Dict[str, Any],
    ):
        super().__init__(callback=callback, on_close=on_close, title=title, size_hint=size_hint, **kwargs)
        self.items1 = items1
        self.items2 = items2
        self.on_change1: Callable[..., Any] | None = on_change1
        self.on_change2: Callable[..., Any] | None = on_change2
        self.auto_dismiss = False

        self._labels1: List[str] = [label for label, _ in items1]
        self._values1: List[Any] = [value for _, value in items1]
        self._labels2: List[str] = [label for label, _ in items2]
        self._values2: List[Any] = [value for _, value in items2]

        self.selected1: Any | None = self._values1[0] if items1 else None
        self.selected2: Any | None = self._values2[0] if items2 else None

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        spinner_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, None), height=44)

        self.spinner1 = Spinner(
            text=self._labels1[0] if self._labels1 else "", values=self._labels1, size_hint=(0.5, 1)
        )
        self.spinner1.bind(text=self._handle_change1)
        spinner_layout.add_widget(self.spinner1)

        self.spinner2 = Spinner(
            text=self._labels2[0] if self._labels2 else "", values=self._labels2, size_hint=(0.5, 1)
        )
        self.spinner2.bind(text=self._handle_change2)
        spinner_layout.add_widget(self.spinner2)

        content.add_widget(spinner_layout)

        btn_layout = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        self.ok_button = Button(text=ok_text)
        self.ok_button.bind(on_release=self.on_ok)
        self.cancel_button = Button(text=cancel_text)
        self.cancel_button.bind(on_release=self.dismiss)  # type:ignore
        btn_layout.add_widget(self.ok_button)
        btn_layout.add_widget(self.cancel_button)
        content.add_widget(btn_layout)

        self.content: BoxLayout = content

    def _handle_change1(self, spinner: Spinner, text: str) -> None:
        if text in self._labels1:
            idx: int = self._labels1.index(text)
            self.selected1 = self._values1[idx]
            if self.on_change1:
                self.on_change1(self.selected1)

    def _handle_change2(self, spinner: Spinner, text: str) -> None:
        if text in self._labels2:
            idx = self._labels2.index(text)
            self.selected2 = self._values2[idx]
            if self.on_change2:
                self.on_change2(self.selected2)

    def on_ok(self, instance: Button) -> None:
        self.done((self.selected1, self.selected2))

    def get_selected(self) -> Tuple[Any, Any]:
        return (self.selected1, self.selected2)

    def _refresh_items(self) -> None:
        self._labels1 = [label for label, _ in self.items1]  # type:ignore
        self._values1 = [value for _, value in self.items1]  # type:ignore
        self.spinner1.values = self._labels1
        if self._labels1:
            self.spinner1.text = self._labels1[0]
            self.selected1 = self._values1[0]

        self._labels2 = [label for label, _ in self.items2]  # type:ignore
        self._values2 = [value for _, value in self.items2]  # type:ignore
        self.spinner2.values = self._labels2
        if self._labels2:
            self.spinner2.text = self._labels2[0]
            self.selected2 = self._values2[0]

    def set_items1(self, items: List[Tuple[str, Any]]) -> None:
        self.items1 = items
        self._refresh_items()

    def set_items2(self, items: List[Tuple[str, Any]]) -> None:
        self.items2 = items
        self._refresh_items()


class MenuPopup(BasePopup):
    items = ListProperty([])  # type:ignore
    on_change = ObjectProperty(None)  # type:ignore

    def __init__(
        self,
        items: List[Tuple[str, Any]],
        callback: Callable[..., Any] | None = None,
        on_change: Callable[..., Any] | None = None,
        on_close: Callable[..., Any] | None = None,
        title: str = "Select Item",
        ok_text: str = "OK",
        cancel_text: str = "Cancel",
        size_hint: Tuple[float, float] = (0.8, 0.4),
        **kwargs: Dict[str, Any],
    ):
        super().__init__(callback=callback, on_close=on_close, size_hint=size_hint, title=title, **kwargs)
        self.items: List[Tuple[str, Any]] = items
        self.on_change: Callable[..., Any] | None = on_change
        self.size_hint = size_hint
        self.auto_dismiss = False
        self._labels: List[str] = [label for label, _ in items]
        self._values: List[Any] = [value for _, value in items]
        self.selected: Any = self._values[0] if items else None

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        initial_label = self._labels[0] if self._labels else ""
        self.spinner = Spinner(text=initial_label, values=self._labels, size_hint=(1, None), height=44)
        self.spinner.bind(text=self._handle_change)
        content.add_widget(self.spinner)

        btn_layout = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        self.ok_button = Button(text=ok_text)
        self.ok_button.bind(on_release=self.on_ok)
        self.cancel_button = Button(text=cancel_text)
        self.cancel_button.bind(on_release=self.dismiss)  # type: ignore
        btn_layout.add_widget(self.ok_button)
        btn_layout.add_widget(self.cancel_button)
        content.add_widget(btn_layout)
        self.content = content

    def _handle_change(self, spinner: Spinner, text: str):
        if text in self._labels:
            idx = self._labels.index(text)
            self.selected = self._values[idx]
            if self.on_change:
                self.on_change(self.selected)

    def on_ok(self, instance: Button) -> None:
        self.done(self.selected)

    def _refresh_items(self):
        self._labels = [label for label, _ in self.items]
        self._values = [value for _, value in self.items]
        self.spinner.values = self._labels
        if self._labels:
            self.spinner.text = self._labels[0]
            self.selected = self._values[0]
        else:
            self.spinner.text = ""
            self.selected = None

    def add_item(self, item: Tuple[str, Any]):
        if item not in self.items:
            self.items.append(item)
            self._refresh_items()

    def insert_item(self, index: int, item: Tuple[str, Any]):
        self.items.insert(index, item)
        self._refresh_items()

    def remove_item(self, item: Tuple[str, Any]):
        if item in self.items:
            was_selected = self.selected
            self.items.remove(item)
            self._refresh_items()
            if was_selected == item[1]:
                self.selected = self._values[0] if self._values else None

    def delete_item_at(self, index: int):
        if 0 <= index < len(self.items):
            removed: Tuple[str, Any] = self.items.pop(index)
            was_selected = self.selected
            self._refresh_items()
            if was_selected == removed[1]:
                self.selected = self._values[0] if self._values else None

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
        **kwargs: Dict[str, Any],
    ):
        super().__init__(callback=callback, size_hint=size_hint, on_close=on_close, title=title, **kwargs)
        self.auto_dismiss = False

        container = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.grid = GridLayout(rows=rows, cols=cols, spacing=5, size_hint=(1, 1))
        container.add_widget(self.grid)

        btn_layout = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        confirm_btn = Button(text="Confirm")
        confirm_btn.bind(on_release=lambda *args: self.done(self._collect_values()))
        cancel_btn = Button(text="Cancel")
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

    def clear_widgets(self):
        self.grid.clear_widgets()

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
        **kwargs: Dict[str, Any],
    ):
        super().__init__(callback=callback, on_close=on_close, title=title, size_hint=size_hint, **kwargs)
        size = len(items)
        if rows <= 0 or cols <= 0:
            cols = int(math.ceil(math.sqrt(size))) if size else 1
            rows = int(math.ceil(size / cols)) if size else 1
        self.auto_dismiss = False

        container = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.grid = GridLayout(rows=rows, cols=cols, spacing=5, size_hint=(1, 1))
        for label, value in items:
            btn = self.create_button(label, value)
            self.grid.add_widget(btn)
        container.add_widget(self.grid)

        btn_layout = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_release=self.dismiss)  # type: ignore
        btn_layout.add_widget(cancel_btn)
        container.add_widget(btn_layout)

        self.content: BoxLayout = container

    def create_button(self, text: str, value: Any) -> Button:
        btn = Button(text=text)
        setattr(btn, "value", value)
        btn.bind(on_release=self._on_button_click)
        return btn

    def _on_button_click(self, instance: Button):
        value = getattr(instance, "value", instance.text)
        self.done(value)
