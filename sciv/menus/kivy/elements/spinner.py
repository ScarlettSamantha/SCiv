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
    dropdown_cls: ObjectProperty[Type[DropDown]]
    option_cls: ObjectProperty[Type[SpinnerOption]]
    values: DictProperty[str, Any]

    def __init__(self, values: Dict[str, Any], **kwargs: Any):
        super(BaseSpinner, self).__init__(**kwargs)
        self.dropdown_cls: ObjectProperty[Type[DropDown]] = DropDown
        self.option_cls: ObjectProperty[Type[SpinnerOption]] = SpinnerOption
        self.values: DictProperty[str, Any] = values

    def _update_dropdown(self, *args: Any, **kwargs: Any):
        dp: DropDown = self._dropdown  # type: ignore
        _cls: Type[ButtonValue] = self.option_cls
        values = self.values
        text_autoupdate = self.text_autoupdate

        if isinstance(_cls, string_types):
            _cls = Factory.get(_cls)  # type: ignore
        dp.clear_widgets()  # type: ignore

        for key, value in values.items():
            item = _cls(text=key, value=value)  # type: ignore
            item.height = self.height if self.sync_height else item.height  # type: ignore
            item.bind(on_release=lambda option: dp.select(option.text))  # type: ignore
            dp.add_widget(item)  # type: ignore

        if text_autoupdate:
            if values:
                if not self.text or self.text not in values:
                    self.text = next(iter(values.keys()))
            else:
                self.text = ""
