from typing import Any, Deque, Dict, Tuple
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle, InstructionGroup  # type: ignore
from kivy.core.text import Label as CoreLabel  # type: ignore
from collections import deque


class ScrollingGraph(Widget):
    def __init__(
        self,
        max_points: int = 300,
        y_max: float = 70.0,
        axis_margin: int = 40,
        num_ticks: int = 5,
        auto_scale: bool = False,
        dynamic_scale: bool = True,
        dynamic_fix: bool = True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)  # type: ignore
        self.max_points: int = max_points
        self.y_max: float = y_max
        self.axis_margin: int = axis_margin
        self.num_ticks: int = num_ticks
        self.auto_scale: bool = auto_scale
        self.dynamic_scale: bool = dynamic_scale
        self.dynamic_fix: bool = dynamic_fix
        self.current_max: float = y_max
        self.running: bool = False

        self.data_sets: Dict[str, Deque[float]] = {
            "fps": deque([0] * max_points, maxlen=max_points),
            "draw": deque([0] * max_points, maxlen=max_points),
            "low1": deque([0] * max_points, maxlen=max_points),
            "frame_ms": deque([0] * max_points, maxlen=max_points),
        }

        self.colors: Dict[str, Tuple[float, ...]] = {
            "fps": (0, 1, 0),
            "draw": (1, 0, 0),
            "low1": (1, 1, 0),
            "frame_ms": (0, 0, 1),
        }

        self.axis_group: InstructionGroup = InstructionGroup()
        self.data_group: InstructionGroup = InstructionGroup()
        self.canvas.before.add(self.axis_group)  # type: ignore
        self.canvas.add(self.data_group)  # type: ignore

        self._lines: Dict[str, Line] = {}
        self._blips: Dict[str, Ellipse] = {}
        for key, color in self.colors.items():
            self.data_group.add(Color(*color))  # type: ignore
            line = Line(points=[], width=1.0)
            self._lines[key] = line
            self.data_group.add(line)  # type: ignore
        for key, color in self.colors.items():
            self.data_group.add(Color(*color))  # type: ignore
            blip = Ellipse(size=(10, 10))  # type: ignore
            self._blips[key] = blip  # type: ignore
            self.data_group.add(blip)  # type: ignore

        self.bind(size=self._redraw_axis, pos=self._redraw_axis)  # type: ignore
        self._redraw_axis()

    def _redraw_axis(self, *_: Any) -> None:
        self.axis_group.clear()

        graph_w = self.width - self.axis_margin  # type: ignore
        graph_h = self.height  # type: ignore

        for i in range(self.num_ticks):
            y = self.y + i / (self.num_ticks - 1) * graph_h  # type: ignore
            self.axis_group.add(Color(1, 1, 1, 0.1))
            self.axis_group.add(Line(points=[self.x + self.axis_margin, y, self.x + self.width, y], width=1))  # type: ignore
            x = self.x + self.axis_margin + i / (self.num_ticks - 1) * graph_w  # type: ignore
            self.axis_group.add(Color(1, 1, 1, 0.1))
            self.axis_group.add(Line(points=[x, self.y, x, self.y + graph_h], width=1))  # type: ignore

        self.axis_group.add(Color(1, 1, 1))

        self.axis_group.add(
            Line(points=[self.x + self.axis_margin, self.y, self.x + self.axis_margin, self.y + graph_h], width=1)  # type: ignore
        )
        self.axis_group.add(Line(points=[self.x + self.axis_margin, self.y, self.x + self.width, self.y], width=1))  # type: ignore

        max_val = self.current_max or 1.0
        for i in range(self.num_ticks):
            val = (i / (self.num_ticks - 1)) * max_val
            y_pos = self.y + (val / max_val) * graph_h  # type: ignore

            self.axis_group.add(Color(1, 1, 1))
            self.axis_group.add(
                Line(points=[self.x + self.axis_margin, y_pos, self.x + self.axis_margin - 5, y_pos], width=1)  # type: ignore
            )

            lbl = CoreLabel(text=f"{int(val)}", font_size=12)  # type: ignore
            lbl.refresh()  # type: ignore
            self.axis_group.add(
                Rectangle(texture=lbl.texture, pos=(self.x, y_pos - lbl.texture.height / 2), size=lbl.texture.size)  # type: ignore
            )

        # Horizontal ticks + labels
        for i in range(self.num_ticks):
            x_pos = self.x + self.axis_margin + i / (self.num_ticks - 1) * graph_w  # type: ignore

            self.axis_group.add(Color(1, 1, 1))
            self.axis_group.add(Line(points=[x_pos, self.y, x_pos, self.y + 5], width=1))  # type: ignore

            if i == self.num_ticks - 1:
                text = "Now"
            else:
                secs_ago = int(self.max_points * (1 - i / (self.num_ticks - 1)))
                text = f"-{secs_ago}s"
            lbl = CoreLabel(text=text, font_size=12)  # type: ignore
            lbl.refresh()  # type: ignore
            self.axis_group.add(
                Rectangle(
                    texture=lbl.texture,  # type: ignore
                    pos=(x_pos - lbl.texture.width / 2, self.y - lbl.texture.height),  # type: ignore
                    size=lbl.texture.size,  # type: ignore
                )
            )

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def stop(self) -> None:
        self.running = False
        for ds in self.data_sets.values():
            ds.clear()
            ds.extend([0] * self.max_points)
        self.current_max = self.y_max
        self._redraw_axis()
        for line in self._lines.values():
            line.points = []  # type: ignore
        for blip in self._blips.values():  # type: ignore
            blip.pos = (self.x + self.axis_margin - 5, self.y - 5)  # type: ignore

    def add_data_point(self, key: str, value: float) -> None:
        if key in self.data_sets:
            self.data_sets[key].append(value)

    def reset(self) -> None:
        self.stop()
        self.start()

    def update_graph(
        self,
        fps: float,
        draw_timing: float,
        low1_fps: float,
        frame_ms: float,
    ) -> None:
        if not self.running:
            return

        if fps >= 3 * self.y_max:
            return

        self.add_data_point("fps", fps)
        self.add_data_point("draw", draw_timing)
        self.add_data_point("low1", low1_fps)

        ms_to_plot = frame_ms
        if self.dynamic_fix and fps > 0:
            theoretical_ms = 1000.0 / fps
            if ms_to_plot > theoretical_ms * 1.5:
                divisor = max(1, int(round(ms_to_plot / theoretical_ms)))
                ms_to_plot /= divisor
        self.add_data_point("frame_ms", ms_to_plot)

        if self.auto_scale:
            max_data = max(max(ds) for ds in self.data_sets.values())
            if max_data > self.y_max:
                self.y_max = max_data
            self.current_max = self.y_max
        elif self.dynamic_scale:
            self.current_max = max(max(ds) for ds in self.data_sets.values()) or self.y_max + 5.0
        else:
            self.current_max = self.y_max

        self._redraw_axis()

        graph_w = self.width - self.axis_margin  # type: ignore
        for key, data in self.data_sets.items():
            pts = []
            for idx, val in enumerate(data):
                x = self.x + self.axis_margin + idx * (graph_w / self.max_points)  # type: ignore
                y = self.y + (val / self.current_max) * self.height  # type: ignore
                pts.extend([x, y])  # type: ignore
            self._lines[key].points = pts  # type: ignore

        for key, data in self.data_sets.items():
            latest = data[-1]
            y_pos = self.y + (latest / self.current_max) * self.height  # type: ignore
            self._blips[key].pos = (self.x + self.axis_margin - 5, y_pos - 5)  # type: ignore
