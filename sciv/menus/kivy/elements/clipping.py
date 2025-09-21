from bisect import bisect_left, bisect_right
from typing import Any, List, Tuple

from helpers.optimizations import throttle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    TOP = 1.0
    BOTTOM = 0.0

    def __init__(
        self,
        cols: int = 1,
        smooth_scroll_speed: float = 0.15,
        invert_scroll: bool = False,
        start_at_bottom: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.do_scroll_y = True
        self.smooth_scroll_speed: float = smooth_scroll_speed
        self.invert_scroll: bool = invert_scroll
        self.start_at_bottom: bool = start_at_bottom
        self.scroll_step_size = 30
        self.bar_width = 12
        self.bar_color: List[int] = [1, 1, 1, 1]

        self._container = GridLayout(cols=cols, size_hint_y=None, padding=5, spacing=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore

        super().add_widget(self._container)

        self._index_dirty: bool = True
        self._indexed: List[Tuple[float, float, Widget]] = []
        self._bottoms: List[float] = []
        self._tops: List[float] = []
        self._visible_start: int = -1
        self._visible_end: int = -1
        self._reindex_scheduled: bool = False

        self.bind(size=self._schedule_reindex, pos=self._schedule_reindex)
        self._container.bind(size=self._schedule_reindex, pos=self._schedule_reindex, children=self._schedule_reindex)

        Clock.schedule_once(self._set_initial_scroll, 0)  # type: ignore
        Clock.schedule_once(self._reindex, 0)  # type: ignore

    def _set_initial_scroll(self, dt: Any):
        if self.start_at_bottom:
            target = self.TOP if self.invert_scroll else self.BOTTOM
        else:
            target = self.BOTTOM if self.invert_scroll else self.TOP
        self.scroll_y = target
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _schedule_reindex(self, *args: Any):
        if self._reindex_scheduled:
            return
        self._reindex_scheduled = True
        Clock.schedule_once(self._reindex, 0)  # type: ignore

    def _reindex(self, dt: Any):
        self._reindex_scheduled = False
        if not self._container.children:
            self._indexed = []
            self._bottoms = []
            self._tops = []
            self._visible_start = -1
            self._visible_end = -1
            return
        self._container.do_layout()  # type: ignore
        items: List[Tuple[float, float, Widget]] = []
        for child in self._container.children:
            bottom_position = float(child.y)
            top_position = bottom_position + float(child.height)
            items.append((bottom_position, top_position, child))
        items.sort(key=lambda it: it[0])
        self._indexed = items
        self._bottoms = [it[0] for it in items]
        self._tops = [it[1] for it in items]
        for _, _, ch in items:
            ch.opacity = 0
        self._visible_start = -1
        self._visible_end = -1
        self._apply_clipping()

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        if widget is self._container:
            super().add_widget(widget, *args, **kwargs)
        else:
            widget.opacity = 0
            self._container.add_widget(widget)
            self._schedule_reindex()

    def remove_widget(self, widget: Widget) -> None:
        if widget is self._container:
            super().remove_widget(widget)
        else:
            self._container.remove_widget(widget)
            self._schedule_reindex()

    def scroll_to_top(self):
        target: float = 0.0 if self.invert_scroll else 1.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_to_bottom(self) -> None:
        target: float = 1.0 if self.invert_scroll else 0.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_by_step(self, direction: str = "up"):
        step: float = self._get_step_size()
        cur: float = float(self.scroll_y)
        content_h: float = float(max(1, int(self._container.height)))
        delta: float = step / content_h
        if (direction == "down") ^ self.invert_scroll:
            new = cur + delta
        else:
            new = cur - delta
        self.scroll_y = max(0.0, min(1.0, new))

    def _get_step_size(self) -> float:
        if self._container.children:
            return float(self._container.children[-1].height)
        return float(self.scroll_step_size)

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        y = float(target_widget.y)
        h = float(target_widget.height)
        content_h = float(max(self._container.height, self.height))
        view_h = float(self.height)
        if content_h > view_h:
            norm = 1.0 - ((y + h) / (content_h - view_h))
        else:
            norm = 1.0
        norm = max(0.0, min(1.0, norm))
        final: float = 1.0 - norm if self.invert_scroll else norm
        Animation(scroll_y=final, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        target_widget_y_position = float(target_widget.y)
        target_widget_height = float(target_widget.height)
        content_h = float(max(self._container.height, self.height))
        view_h = float(self.height)
        if content_h > view_h:
            norm = 1.0 - ((target_widget_y_position + target_widget_height) / (content_h - view_h))
        else:
            norm = 1.0
        norm = max(0.0, min(1.0, norm))
        self.scroll_y = 0.0 + norm if self.invert_scroll else norm

    def clear_widgets(self, children: List[Widget] | None = None):
        self._container.clear_widgets(children=children)
        self._schedule_reindex()

    def on_scroll_y(self, *args: Any):
        self._apply_clipping()

    @throttle(0.05, True)
    def _apply_clipping(self, *args: Any):
        if not self._indexed:
            return
        self._container.do_layout()  # type: ignore
        content_h = float(self._container.height)
        view_h = float(self.height)
        self.do_scroll_y = content_h > view_h
        if not self.do_scroll_y:
            if self._visible_start != 0 or self._visible_end != len(self._indexed) - 1:
                for _, _, ch in self._indexed:
                    ch.opacity = 1
                self._visible_start = 0
                self._visible_end = len(self._indexed) - 1
            return
        v_bottom = (content_h - view_h) * float(self.scroll_y)
        v_top = v_bottom + view_h
        start = bisect_right(self._tops, v_bottom)
        end = bisect_left(self._bottoms, v_top) - 1
        if end < start:
            new_s, new_e = -1, -1
        else:
            new_s, new_e = start, end
        if new_s == self._visible_start and new_e == self._visible_end:
            return
        if self._visible_start != -1:
            a = self._visible_start
            b = self._visible_end
            inter_s = max(a, new_s) if new_s != -1 else None
            inter_e = min(b, new_e) if new_e != -1 else None
            if inter_s is None or inter_e is None or inter_s > inter_e:
                for i in range(a, b + 1):
                    self._indexed[i][2].opacity = 0
            else:
                for i in range(a, inter_s):
                    self._indexed[i][2].opacity = 0
                for i in range(inter_e + 1, b + 1):
                    self._indexed[i][2].opacity = 0
        if new_s != -1:
            if self._visible_start == -1:
                for i in range(new_s, new_e + 1):
                    self._indexed[i][2].opacity = 1
            else:
                a = self._visible_start
                b = self._visible_end
                if new_s < a:
                    for i in range(new_s, min(a, new_e + 1)):
                        self._indexed[i][2].opacity = 1
                if new_e > b:
                    for i in range(max(b + 1, new_s), new_e + 1):
                        self._indexed[i][2].opacity = 1
        self._visible_start = new_s
        self._visible_end = new_e


class HorizontalClippingScrollList(ScrollView):
    def __init__(self, rows: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.do_scroll_x = True
        self.do_scroll_y = False
        self.smooth_scroll_speed: float = smooth_scroll_speed
        self.bar_width = 12
        self.bar_color: List[int] = [1, 1, 1, 1]

        self._container = GridLayout(rows=rows, size_hint_x=None, padding=5, spacing=5)
        self._container.bind(minimum_width=self._container.setter("width"))  # type: ignore

        self.add_widget(self._container)

        self._index_dirty: bool = True
        self._indexed: List[Tuple[float, float, Widget]] = []
        self._lefts: List[float] = []
        self._rights: List[float] = []
        self._visible_start: int = -1
        self._visible_end: int = -1
        self._reindex_scheduled: bool = False

        self.bind(size=self._schedule_reindex, pos=self._schedule_reindex)
        self._container.bind(size=self._schedule_reindex, pos=self._schedule_reindex, children=self._schedule_reindex)

        Clock.schedule_once(self._reindex, 0)  # type: ignore

    def _schedule_reindex(self, *args: Any):
        if self._reindex_scheduled:
            return
        self._reindex_scheduled = True
        Clock.schedule_once(self._reindex, 0)  # type: ignore

    def _reindex(self, dt: Any):
        self._reindex_scheduled = False
        if not self._container.children:
            self._indexed = []
            self._lefts = []
            self._rights = []
            self._visible_start = -1
            self._visible_end = -1
            return
        self._container.do_layout()  # type: ignore
        items: List[Tuple[float, float, Widget]] = []
        for child in self._container.children:
            left_coordinate = float(child.x)
            right_coordinate = left_coordinate + float(child.width)
            items.append((left_coordinate, right_coordinate, child))
        items.sort(key=lambda it: it[0])
        self._indexed = items
        self._lefts = [it[0] for it in items]
        self._rights = [it[1] for it in items]
        for _, _, ch in items:
            ch.opacity = 0
        self._visible_start = -1
        self._visible_end = -1
        self._apply_clipping()

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        if widget != self._container:
            widget.opacity = 0
            self._container.add_widget(widget)
            self._schedule_reindex()
        else:
            super().add_widget(widget, *args, **kwargs)  # type: ignore

    def remove_widget(self, widget: Widget) -> None:
        if widget is self._container:
            super().remove_widget(widget)
        else:
            self._container.remove_widget(widget)
            self._schedule_reindex()

    def on_scroll_x(self, *args: Any):
        self._apply_clipping()

    def force_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        content_width = float(self._container.width)  # type: ignore
        target_left = float(target_widget.x)  # type: ignore
        visible_space = max(1.0, content_width - float(self.width))  # type: ignore
        new_scroll = target_left / float(visible_space)  # type: ignore
        self.scroll_x = max(0.0, min(1.0, new_scroll))  # type: ignore

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        content_width = float(self._container.width)  # type: ignore
        target_left = float(target_widget.x)  # type: ignore
        visible_space = max(1.0, content_width - float(self.width))  # type: ignore
        new_scroll = target_left / float(visible_space)  # type: ignore
        new_scroll = max(0.0, min(1.0, new_scroll))  # type: ignore
        Animation(scroll_x=new_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)  # type: ignore

    def scroll_to_left(self):
        self.scroll_x = 0.0

    def scroll_to_right(self):
        self.scroll_x = 1.0

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        self._schedule_reindex()

    @throttle(0.05, True)
    def _apply_clipping(self, *args: Any):
        if not self._indexed:
            return
        self._container.do_layout()  # type: ignore
        content_w = float(self._container.width)  # type: ignore
        view_w = float(self.width)  # type: ignore
        self.do_scroll_x = content_w > view_w  # type: ignore
        if not self.do_scroll_x:
            if self._visible_start != 0 or self._visible_end != len(self._indexed) - 1:
                for _, _, ch in self._indexed:
                    ch.opacity = 1
                self._visible_start = 0
                self._visible_end = len(self._indexed) - 1
            return
        v_left = (content_w - view_w) * float(self.scroll_x)
        v_right = v_left + view_w
        start = bisect_right(self._rights, v_left)
        end = bisect_left(self._lefts, v_right) - 1
        if end < start:
            new_s, new_e = -1, -1
        else:
            new_s, new_e = start, end
        if new_s == self._visible_start and new_e == self._visible_end:
            return
        if self._visible_start != -1:
            a = self._visible_start
            b = self._visible_end
            inter_s = max(a, new_s) if new_s != -1 else None
            inter_e = min(b, new_e) if new_e != -1 else None
            if inter_s is None or inter_e is None or inter_s > inter_e:
                for i in range(a, b + 1):
                    self._indexed[i][2].opacity = 0
            else:
                for i in range(a, inter_s):
                    self._indexed[i][2].opacity = 0
                for i in range(inter_e + 1, b + 1):
                    self._indexed[i][2].opacity = 0
        if new_s != -1:
            if self._visible_start == -1:
                for i in range(new_s, new_e + 1):
                    self._indexed[i][2].opacity = 1
            else:
                a = self._visible_start
                b = self._visible_end
                if new_s < a:
                    for i in range(new_s, min(a, new_e + 1)):
                        self._indexed[i][2].opacity = 1
                if new_e > b:
                    for i in range(max(b + 1, new_s), new_e + 1):
                        self._indexed[i][2].opacity = 1
        self._visible_start = new_s
        self._visible_end = new_e
