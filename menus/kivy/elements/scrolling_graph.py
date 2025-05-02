from typing import Any, Deque, Dict, Tuple
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle  # type: ignore
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
        # current_max is the value used for scaling/drawing axes
        self.current_max: float = y_max

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

        # redraw axis when resized or moved
        self.bind(size=self._redraw_axis, pos=self._redraw_axis)  # type: ignore

    def _redraw_axis(self, *_: Any) -> None:
        """
        Draw the vertical axis, tick marks, and labels based on current_max.
        """
        self.canvas.before.clear()  # type: ignore
        with self.canvas.before:  # type: ignore
            Color(1, 1, 1)
            # vertical axis line
            Line(
                points=[
                    self.x + self.axis_margin,  # type: ignore
                    self.y,  # type: ignore
                    self.x + self.axis_margin,  # type: ignore
                    self.y + self.height,  # type: ignore
                ],
                width=1,
            )  # type: ignore

            # ticks + labels
            max_val = self.current_max or 1.0
            for i in range(self.num_ticks):
                val = (i / (self.num_ticks - 1)) * max_val
                y_pos = self.y + (val / max_val) * self.height  # type: ignore

                Line(
                    points=[
                        self.x + self.axis_margin,  # type: ignore
                        y_pos,
                        self.x + self.axis_margin - 5,  # type: ignore
                        y_pos,
                    ],
                    width=1,
                )  # type: ignore
                lbl = CoreLabel(text=f"{int(val)}", font_size=12)  # type: ignore
                lbl.refresh()  # type: ignore
                Rectangle(
                    texture=lbl.texture,  # type: ignore
                    pos=(self.x, y_pos - lbl.texture.height / 2),  # type: ignore
                    size=lbl.texture.size,  # type: ignore
                )  # type: ignore

    def add_data_point(self, key: str, value: float) -> None:
        if key in self.data_sets:
            self.data_sets[key].append(value)

    def update_graph(
        self,
        fps: float,
        draw_timing: float,
        low1_fps: float,
        frame_ms: float,
    ) -> None:
        if fps >= 3 * self.y_max:
            return
        # push new values
        self.add_data_point("fps", fps)
        self.add_data_point("draw", draw_timing)
        self.add_data_point("low1", low1_fps)

        # correct frame_ms for update interval if requested
        ms_to_plot = frame_ms
        if self.dynamic_fix and fps > 0:
            theoretical_ms = 1000.0 / fps
            # if reported frame_ms is significantly higher, assume multiple frames aggregated
            if ms_to_plot > theoretical_ms * 1.5:
                divisor = max(1, int(round(ms_to_plot / theoretical_ms)))
                ms_to_plot = ms_to_plot / divisor
        self.add_data_point("frame_ms", ms_to_plot)

        # determine scaling
        if self.auto_scale:
            # permanently increase y_max if data exceeds it
            max_data = max(max(ds) for ds in self.data_sets.values())
            if max_data > self.y_max:
                self.y_max = max_data
            self.current_max = self.y_max
        elif self.dynamic_scale:
            # scale just for this frame to fullest range
            self.current_max = max(max(ds) for ds in self.data_sets.values()) or self.y_max + 5.0
        else:
            # fixed scale
            self.current_max = self.y_max

        # redraw axis with updated scale
        self._redraw_axis()

        # draw lines and blips
        self.canvas.clear()  # type: ignore
        with self.canvas:  # type: ignore
            graph_w = self.width - self.axis_margin  # type: ignore

            # draw all series
            for key, data in self.data_sets.items():
                Color(*self.colors[key])  # type: ignore
                pts: list[float] = []
                for i, y in enumerate(data):
                    x_pos = self.x + self.axis_margin + i * (graph_w / self.max_points)  # type: ignore
                    y_pos = self.y + (y / self.current_max) * self.height  # type: ignore
                    pts.extend([x_pos, y_pos])  # type: ignore
                if len(pts) >= 4:
                    Line(points=pts, width=1.0)

            # draw the latest-value “blip” on the axis for each series
            for key, ds in self.data_sets.items():
                latest = ds[-1]
                y_pos = self.y + (latest / self.current_max) * self.height  # type: ignore
                Color(*self.colors[key])  # type: ignore
                Ellipse(
                    pos=(self.x + self.axis_margin - 5, y_pos - 5),  # type: ignore
                    size=(10, 10),
                )  # type: ignore
