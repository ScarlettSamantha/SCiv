from kivy.uix.spinner import Spinner as BaseSpinner
from menus.kivy.elements.dropdown import DropDown
from kivy.properties import ObjectProperty


class Spinner(BaseSpinner):
    dropdown_cls = ObjectProperty(DropDown)
