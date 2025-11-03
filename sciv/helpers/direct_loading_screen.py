from random import choice
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional

from direct.gui.DirectGui import DirectButton, DirectWaitBar, OnscreenImage, OnscreenText
from direct.interval.LerpInterval import LerpFunc
from direct.task.Task import Task
from helpers.os import WindowsHelper
from panda3d.core import CardMaker, NodePath, TextNode, TransparencyAttrib

if TYPE_CHECKING:
    from game import OpenCiv


class LoadingScreen:
    def __init__(
        self,
        base: "OpenCiv",
        logo_paths: list[str],
        total_steps: int,
        on_continue: Optional[Callable[..., None]] = None,
    ):
        self.base = base
        self.total_steps = max(1, total_steps)
        self.current_step = 0
        self.on_continue = on_continue
        self.continue_button = None

        # Fullscreen black background
        cm = CardMaker("bg")
        cm.setFrameFullscreenQuad()
        self.bg = NodePath(cm.generate())  # type: ignore
        self.bg.setColor(0, 0, 0, 1)
        self.bg.reparentTo(base.render2d)  # type: ignore

        # Logo image
        logo_path = choice(logo_paths)

        if WindowsHelper.is_windows():
            logo_path = WindowsHelper.win32_to_unix_path(logo_path)

        self.logo = OnscreenImage(
            image=logo_path,
            pos=(0, 0, 0.55),
            scale=(0.5, 0.5, 0.5),
        )
        self.logo.setTransparency(TransparencyAttrib.MAlpha)
        self.logo.setScale(self._scale_logo(self.logo.getImage()))

        font_path = str(self.base.base_path / "assets" / "fonts" / "OpenSans.ttf")

        if WindowsHelper.is_windows():
            font_path = WindowsHelper.win32_to_unix_path(font_path)

        # Step count
        self.step_count = OnscreenText(
            text=f"0/{self.total_steps}",
            pos=(0, -0.55),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,  # type: ignore
            mayChange=True,
        )

        # Progress bar
        self.bar = DirectWaitBar(
            text="",
            value=0,
            range=100,
            pos=(0, 0, -0.65),
            barColor=(0.3, 0.6, 0.9, 1),
            frameColor=(0.15, 0.15, 0.15, 1),
            frameSize=(-0.7, 0.7, -0.05, 0.05),
            scale=1.0,
        )

        # Pulse animation
        self.base.taskMgr.add(self._pulse_task, "loading-pulse")

    def next_stage(self, message: str):
        self.current_step += 1
        percent = min((self.current_step / self.total_steps) * 100, 100)

        self.step_count.setText(f"{round(percent, 2)}% ({self.current_step}/{self.total_steps}): {message}")
        self.bar["value"] = percent

        # If done, show continue
        if self.current_step >= self.total_steps and not self.continue_button:
            self._show_continue_button()

    def _show_continue_button(self):
        self.continue_button = DirectButton(
            text="Continue",
            scale=(0.25, 0.25, 0.08),
            pos=(0, 0, -0.8),
            frameColor=(0.2, 0.4, 0.8, 0),
            text_fg=(1, 1, 1, 0),
            pad=(0.04, 0.02),
            command=self._on_continue_clicked,
        )
        self._fade_in_button()

    def _fade_in_button(self):
        def fade(alpha: float):
            if self.continue_button:
                self.continue_button["frameColor"] = (0.2, 0.4, 0.8, alpha)
                self.continue_button["text_fg"] = (1, 1, 1, alpha)

        LerpFunc(fade, fromData=0, toData=1, duration=1.0, blendType="easeInOut", name="fade-continue-btn").start()

    def _on_continue_clicked(self):
        self.destroy()
        if self.on_continue:
            self.on_continue()

    def destroy(self):
        self.base.taskMgr.remove("loading-pulse")
        self.bar.destroy()
        self.logo.destroy()
        self.step_count.destroy()
        self.bg.removeNode()
        if self.continue_button:
            self.continue_button.destroy()

    def _scale_logo(self, tex: OnscreenImage) -> float | tuple[float, Literal[1], Any]:
        if not tex:
            return 0.5
        aspect = tex.getTexture().getXSize() / tex.getTexture().getYSize()
        width = 0.5
        height = width / aspect
        return (width, 1, height)

    def _pulse_task(self, task: Task):
        from math import pi, sin

        pulse = (sin(task.time * pi) + 1) / 2
        base_color = (0.3, 0.6, 0.9)
        pulse_strength = 0.05
        r = base_color[0] + pulse_strength * pulse
        g = base_color[1] + pulse_strength * pulse
        b = base_color[2] + pulse_strength * pulse
        self.bar["barColor"] = (r, g, b, 1)
        return task.cont
