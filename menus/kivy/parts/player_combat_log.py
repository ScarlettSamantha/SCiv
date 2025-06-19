from typing import Any, List
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from direct.showbase.DirectObject import DirectObject
from managers.combat_log import CombatLogEntry
from menus.kivy.elements.clipping import ClippingScrollList


class PlayerCombatLog(BoxLayout, DirectObject):
    def __init__(self, log: List[CombatLogEntry], **kwargs: Any):
        kwargs.setdefault("size_hint", (0.3, 0.2))
        kwargs.setdefault("pos", (0, 0))
        kwargs.setdefault("pos_hint", {"right": 0.935, "top": 0.21})
        super().__init__(orientation="vertical", spacing=dp(4), padding=dp(4), **kwargs)

        self.logRef: List[CombatLogEntry] = log
        self.is_built: bool = False
        self.scroll: ClippingScrollList | None = None
        self.bg_rect: Rectangle | None = None
        self.disabled = False

        self.register()

    def register(self):
        self.accept("ui.update.ui.combat_log.add", self.add_entry)

    def build(self):
        if self.is_built:
            return

        # Header label
        header = Label(text="[b]Combat Log[/b]", markup=True, size_hint_y=None, height=dp(32))
        self.add_widget(header)

        self.scroll = ClippingScrollList(
            cols=1, smooth_scroll_speed=0.05, size_hint=(1, 1), bar_width=dp(4), invert_scroll=False
        )

        with self.canvas.before:
            Color(0, 0, 0, 0.7)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)  # type: ignore

        self.bind(
            size=lambda inst, val: setattr(self.bg_rect, "size", val),
            pos=lambda inst, val: setattr(self.bg_rect, "pos", val),
        )

        self.add_widget(self.scroll)
        self.is_built = True

    def update(self):
        if self.scroll:
            self.scroll.clear_widgets()

            for entry in self.logRef:
                ts = entry.timestamp.strftime("%H:%M:%S")
                line = f"[{ts}]: {entry.text}"

                lbl = Label(text=line, markup=True, size_hint_y=None)

                lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - dp(24), None)))  # type: ignore
                lbl.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))  # type: ignore

                self.scroll.add_widget(lbl)

            # Scroll to bottom to show the latest entries
            self.scroll.scroll_to_bottom()

    def add_entry(self, entry: CombatLogEntry):
        self.logRef.append(entry)
        line = f"[{entry.timestamp.strftime('%H:%M:%S')}]: {entry.text}"

        lbl = Label(text=line, markup=True, size_hint_y=None)

        lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - dp(24), None)))  # type: ignore
        lbl.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))  # type: ignore

        self.scroll.add_widget(lbl)  # type: ignore
        self.scroll.scroll_to_bottom()  # type: ignore
