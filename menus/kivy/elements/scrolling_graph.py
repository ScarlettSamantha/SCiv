from typing import Any, Deque, Dict
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from collections import deque


class ScrollingGraph(Widget):
    def __init__(self, max_points: float = 200, y_max: float = 60.0, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.max_points: float = max_points
        self.y_max: float = y_max  # Maximum Y-axis value for scaling
        self.data_sets: Dict[str, Deque[float]] = {
            "fps": deque([0] * int(max_points), maxlen=int(max_points)),
            "draw": deque([0] * int(max_points), maxlen=int(max_points)),
        }
        self.colors = {
            "fps": (0, 1, 0),  # green
            "draw": (1, 0, 0),  # red
        }

    def add_data_point(self, key: str, value: float) -> None:
        if key in self.data_sets:
            self.data_sets[key].append(value)

    def update_graph(self, dt: float, fps: float, timing: float) -> None:
        self.add_data_point("fps", fps)
        self.add_data_point("draw", timing)

        self.canvas.clear()  # type: ignore
        with self.canvas:  # type: ignore
            for key, data in self.data_sets.items():
                Color(*self.colors[key])
                points = []
                for i, y in enumerate(iterable=data):
                    x = self.x + i * (self.width / self.max_points)  # type: ignore
                    y_scaled = self.y + (y / self.y_max) * self.height  # type: ignore
                    points.extend([x, y_scaled])  # type: ignore
                if len(points) >= 4:  # type: ignore
                    Line(points=points, width=1.2)
