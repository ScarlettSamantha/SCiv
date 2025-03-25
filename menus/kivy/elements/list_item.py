from menus.kivy.elements.button_value import ButtonValue


class ListItem(ButtonValue):
    def __init__(self, background_color=(1, 1, 1, 0.3), halign="left", valign="bottom", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_normal = ""  # delete background texture
        self.background_down = ""  # delete background texture
        self.background_color = background_color  # Default texture is a gray block so it will darken the color
        self.halign = halign
        self.valign = valign
        self.padding_x = 10
        self.padding_y = 5

        self.bind(
            size=self._update_text_size
        )  # This is done so we can use halign and valign as its a label in the button

    def _update_text_size(self, *args):
        # Set text_size to the current width to enable proper alignment
        self.text_size = (self.width, None)  # type: ignore
