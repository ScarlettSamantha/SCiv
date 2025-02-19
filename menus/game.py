from typing import Union
import math

from direct.gui.DirectGui import DirectFrame, DirectLabel
from httpx import head
from panda3d.core import LineSegs, NodePath, TextNode
from menus._base import BaseMenu
from camera import CivCamera


def create_circle(radius=0.1, num_segments=32, color=(1, 1, 1, 1)):
    """
    Approximate a circle using LineSegs.
    """
    segs = LineSegs()
    segs.setColor(*color)
    segs.setThickness(2.0)

    angle_step = 2 * math.pi / num_segments
    for i in range(num_segments + 1):
        angle = i * angle_step
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        if i == 0:
            segs.moveTo(x, 0, z)
        else:
            segs.drawTo(x, 0, z)

    return segs.create()


def create_arrow_line(length=0.08, color=(1, 0, 0, 1)):
    """
    Create a simple line from (0,0,0) to (0,0,length).
    We'll rotate this line in the plane, so it acts like an arrow.
    """
    segs = LineSegs()
    segs.setColor(*color)
    segs.setThickness(2.0)
    segs.moveTo(0, 0, 0)
    segs.drawTo(0, 0, length)
    return segs.create()


class Game(BaseMenu):
    def __init__(self, base):
        super().__init__()
        self.base = base

        # UI references
        self.frame = None
        self.label = None
        self.fps_label = None

        # Compass geometry references
        self.compass_parent = None
        self.compass_circle = None
        self.compass_arrow = None

        self._camera: CivCamera = CivCamera.get_instance()

    def register(self):
        # Listen for "ui.update.user.tile_clicked" event if needed
        self.base.accept("ui.update.user.tile_clicked", self.process_game_click)

    def show(self):
        """Set up all GUI elements."""
        from managers.ui import ui

        ui.get_instance().get_main_menu

        # Create the frame
        self.frame = DirectFrame(
            parent=self.base.a2dTopRight,
            frameColor=(0.2, 0.2, 0.2, 1),
            frameSize=(-0.1, 0.5, -0.2, 0.4),  # (left, right, bottom, top)
            pos=(-0.50, -0.4, -0.4),
        )

        # Retrieve the frame boundaries
        left, right, bottom, top = self.frame["frameSize"]

        # Small offset so the label isn't flush against the corner
        offset_x = 0.02
        offset_z = 0.05

        # Create a label pinned to top-left corner of the frame
        self.label = DirectLabel(
            parent=self.frame,
            text="Initial text",
            text_scale=0.05,
            text_align=TextNode.ALeft,  # anchor text at its left edge
            pos=(left + offset_x, 0, top - offset_z),
            frameColor=(0, 0, 0, 0),  # make label background transparent
        )

        # FPS label in the top-left corner
        self.fps_label = DirectLabel(
            parent=self.base.a2dTopLeft,  # Anchor to the top-left corner
            text="FPS: 0",
            text_scale=0.04,
            pos=(0.10, 0, -0.05),  # Small offset right (X) and down (Z)
            frameColor=(0, 0, 0, 0),  # Make label background transparent
        )

        # --- Create compass geometry in aspect2d ---
        self.compass_parent = NodePath("compass_parent")
        self.compass_parent.reparentTo(self.base.aspect2d)

        # Position it near the top-left corner
        self.compass_parent.setPos(-1.7, 0, 0.85)

        # Draw a small circle
        circle_geom = create_circle(radius=0.05, color=(1, 1, 1, 1))
        self.compass_circle = NodePath(circle_geom)
        self.compass_circle.reparentTo(self.compass_parent)

        # Draw an arrow line we can rotate
        arrow_geom = create_arrow_line(length=0.05, color=(1, 0, 0, 1))
        self.compass_arrow = NodePath(arrow_geom)
        self.compass_arrow.reparentTo(self.compass_parent)

        # Add a task to update FPS and arrow rotation
        self.base.taskMgr.add(self.update_compass_and_fps, "update_compass_and_fps")

        return self.frame

    def update_compass_and_fps(self, task):
        """Task to update the FPS label and rotate the arrow."""
        # 1) Update FPS
        fps = self.base.clock.getAverageFrameRate()
        if self.fps_label is not None:
            self.fps_label["text"] = f"FPS: {fps:.2f}"

        # 2) Rotate the arrow so it remains pointing 'north' as the camera spins.
        heading = self._camera.yaw % 360
        # For geometry that goes "up" in aspect2d, rotate around the Y-axis with setR(...)
        # Instead of using negative, we subtract heading from 360 to inverse the rotation direction.
        if self.compass_arrow is not None:
            self.compass_arrow.setR(-heading)

        return task.cont

    def update_label_text(self, new_text: Union[list[str], str]):
        """Helper to update the text of the frame label."""
        if not self.label:
            return
        if isinstance(new_text, str):
            self.label["text"] = new_text
        else:
            self.label["text"] = "\n".join(new_text)

    def process_game_click(self, tile: Union[list[str], str]):
        """Example method triggered when a tile is clicked."""
        if isinstance(tile, str):
            tile = [tile]
        self.update_label_text(tile)
