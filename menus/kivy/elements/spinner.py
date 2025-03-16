from typing import Any, Dict, Type

from kivy.compat import string_types
from kivy.factory import Factory
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.spinner import Spinner as BaseSpinner

from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.dropdown import DropDown


class SpinnerOption(ButtonValue):
    """Special button used in the :class:`Spinner` dropdown list. By default,
    this is just a :class:`~kivy.uix.button.Button` with a size_hint_y of None
    and a height of :meth:`48dp <kivy.metrics.dp>`.
    """

    ...


class ValueSpinner(BaseSpinner):
    dropdown_cls = ObjectProperty(DropDown)
    option_cls = ObjectProperty(SpinnerOption)
    values = DictProperty()

    def __init__(self, values: Dict[str, Any], **kwargs):
        super(BaseSpinner, self).__init__(**kwargs)
        self.dropdown_cls = DropDown
        self.option_cls = SpinnerOption
        self.values = values

    def _update_dropdown(self, *largs):
        dp = self._dropdown
        cls: Type[ButtonValue] = self.option_cls
        values = self.values
        text_autoupdate = self.text_autoupdate
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        dp.clear_widgets()  # type: ignore
        for key, value in values.items():
            item = cls(text=key, value=value)
            item.height = self.height if self.sync_height else item.height
            item.bind(on_release=lambda option: dp.select(option.text))  # type: ignore
            dp.add_widget(item)  # type: ignore
        if text_autoupdate:
            if values:
                if not self.text or self.text not in values:
                    self.text = next(iter(values.keys()))
            else:
                self.text = ""
