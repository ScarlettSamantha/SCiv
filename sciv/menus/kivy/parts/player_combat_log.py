from typing import TYPE_CHECKING, Any, List, Optional

from direct.showbase.DirectObject import DirectObject
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from managers.combat_log import CombatLogEntry
from managers.i18n import t_
from menus.kivy.elements.clipping import ClippingScrollList

if TYPE_CHECKING:
    from game import OpenCiv


class PlayerCombatLog(BoxLayout, DirectObject):
    def __init__(self, log: List[CombatLogEntry], base: "OpenCiv", **kwargs: Any):
        screen_width, screen_height = base.win.getXSize(), base.win.getYSize()  # type: ignore
        self.base = base

        kwargs.setdefault("width", dp(850))
        kwargs.setdefault("height", dp(300))
        kwargs.setdefault("pos", (dp(int(screen_width - 1075)), dp(10)))
        kwargs.setdefault("size_hint", (None, None))

        super().__init__(orientation="vertical", spacing=dp(4), padding=dp(4), **kwargs)

        self.logRef: List[CombatLogEntry] = log
        self.is_built: bool = False
        self.scroll: Optional[ClippingScrollList] = None
        self.bg_rect: Optional[Rectangle] = None
        self.disabled = False

        self._expanded_height: float = float(self.height)
        self._compact_height: float = dp(100)
        self._compact_max_entries: int = 100
        self._is_compact: bool = True
        self.height = self._compact_height

        self._header_btn: Optional[Button] = None
        self._header_lbl: Optional[Label] = None

        self.register()

    def register(self):
        self.accept("ui.update.ui.combat_log.add", self.add_entry)

    def build(self):
        if self.is_built:
            return

        with self.canvas.before:
            Color(0, 0, 0, 0.7)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)  # type: ignore

        self.bind(
            size=lambda inst, val: setattr(self.bg_rect, "size", val) if self.bg_rect else None,
            pos=lambda inst, val: setattr(self.bg_rect, "pos", val) if self.bg_rect else None,
        )

        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(6), padding=(0, 0))
        self._header_lbl = Label(text="[b]Combat Log[/b]", markup=True, halign="left", valign="middle")
        self._header_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore

        self._header_btn = Button(
            text="Expand" if self._is_compact else f"Compact ({self._compact_max_entries})",
            size_hint=(None, 1),
            width=dp(140),
        )
        self._header_btn.bind(on_release=lambda *_: self.toggle_compact())  # type: ignore

        header_row.add_widget(self._header_lbl)
        header_row.add_widget(self._header_btn)
        self.add_widget(header_row)

        self.scroll = ClippingScrollList(
            cols=1,
            smooth_scroll_speed=0.05,
            size_hint=(1, 1),
            bar_width=dp(4),
            invert_scroll=False,
        )
        self.add_widget(self.scroll)

        self.is_built = True
        self.update()

    def update(self):
        if not self.scroll:
            return

        self.scroll.clear_widgets()

        entries: List[CombatLogEntry] = self._current_entries()
        for entry in entries:
            ts = entry.timestamp.strftime("%H:%M:%S")
            line = f"[{ts}]: {entry.text}"
            lbl = Label(text=line, markup=True, size_hint_y=None)
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - dp(24), None)))  # type: ignore
            lbl.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))  # type: ignore
            self.scroll.add_widget(lbl)

        self.scroll.scroll_to_bottom()

    def add_entry(self, entry: CombatLogEntry):
        self.logRef.append(entry)

        if not self.is_built or not self.scroll:
            return

        self.update()

    def toggle_compact(self):
        self._is_compact = not self._is_compact

        target_h = int(self._compact_height if self._is_compact else self._expanded_height)
        self.height = target_h

        if self._header_btn:
            if self._is_compact:
                self._header_btn.text = str(t_("ui.player_ui.combat_log.expand"))
            else:
                self._header_btn.text = str(
                    t_("ui.player_ui.combat_log.compact", {"max_entries": self._compact_max_entries})
                )

        self.update()

    def _current_entries(self) -> List[CombatLogEntry]:
        if not self._is_compact:
            return self.logRef
        n = self._compact_max_entries
        return self.logRef[-n:] if len(self.logRef) > n else self.logRef
