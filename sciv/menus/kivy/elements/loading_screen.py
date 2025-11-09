from typing import Any, Callable, List, Optional, Tuple

from helpers.cache import Cache
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from system.asset_archive import P3DAssetArchive

from helpers.icons import Icons


class LoadingScreen(FloatLayout):
    total_steps = NumericProperty(1)
    current_step = NumericProperty(0)
    step_message = StringProperty("Loading...")
    show_continue = BooleanProperty(False)

    loading_screen_image: List[str] = Icons.loading_screens(True)

    def __init__(self, on_complete: Callable[..., None], **kwargs: Any):
        super().__init__(**kwargs)
        self.on_complete = on_complete

        self.assets: P3DAssetArchive = Cache.get_asset_archive()

        with self.canvas.before:  # type: ignore
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(pos=self._update_bg, size=self._update_bg)  # type: ignore

        self.bg_image = self.assets.get_kivy_image_object(
            virtual_path=self.loading_screen_image[0],
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={"top": 1},
        )
        self.add_widget(self.bg_image)

        overlay_box = BoxLayout(
            orientation="horizontal",
            size_hint=(1, 0.9),
            pos_hint={"top": 1},
            padding=dp(30),
            spacing=dp(20),  # type: ignore
        )

        self.left_overlay = Image(source="", size_hint=(0.2, 1), opacity=0.3)
        overlay_box.add_widget(self.left_overlay)

        center_stack = BoxLayout(orientation="vertical", size_hint=(0.6, 1), padding=dp(10))
        self.logo_image = self.assets.get_kivy_image_object(
            virtual_path=Icons.game_logo_512(),
            size_hint=(None, None),
            size=(dp(256), dp(256)),
            pos_hint={"top": 1, "center_x": 0.5},
        )

        center_stack.add_widget(self.logo_image)
        center_stack.add_widget(Widget())  # Spacer
        overlay_box.add_widget(center_stack)

        self.right_overlay = BoxLayout(orientation="vertical", size_hint=(0.2, 1), padding=dp(10), spacing=dp(10))  # type: ignore
        with self.right_overlay.canvas.before:
            Color(1, 1, 1, 0.25)
            self.right_frame = RoundedRectangle(  # type: ignore
                radius=[dp(8)], pos=self.right_overlay.pos, size=self.right_overlay.size
            )

        self.right_overlay.bind(pos=self._update_right_frame, size=self._update_right_frame)  # type: ignore

        self.right_content_container = AnchorLayout(
            anchor_x="center",
            anchor_y="top",
        )

        self.right_content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),  # type: ignore
            size_hint_y=None,
        )
        self.right_content.bind(minimum_height=self.right_content.setter("height"))  # type: ignore

        self.right_content_container.add_widget(self.right_content)
        self.right_overlay.add_widget(self.right_content_container)
        overlay_box.add_widget(self.right_overlay)

        self.add_widget(overlay_box)

        bottom_panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, 0.1),
            padding=dp(20),
            spacing=dp(10),  # type: ignore
            pos_hint={"y": 0},  # type: ignore
        )

        self.step_label = Label(text=self.step_message, font_size="18sp", color=(1, 1, 1, 1), size_hint_y=None)
        self.step_label.bind(texture_size=self._resize_label)  # type: ignore
        bottom_panel.add_widget(self.step_label)

        progress_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(10))  # type: ignore
        self.progress_bar = ProgressBar(max=1, value=0)
        self.percentage_label = Label(text="0%", color=(1, 1, 1, 1), size_hint_x=None, width=dp(50))  # type: ignore
        progress_box.add_widget(self.progress_bar)
        progress_box.add_widget(self.percentage_label)
        bottom_panel.add_widget(progress_box)

        self.continue_button = Button(text="Continue", size_hint_y=None, height=dp(40), opacity=0, disabled=True)  # type: ignore
        self.continue_button.bind(on_press=self._handle_complete)  # type: ignore
        bottom_panel.add_widget(self.continue_button)

        self.add_widget(bottom_panel)

        Clock.schedule_once(self._update_ui)  # type: ignore

    def _resize_label(self, instance: Widget, size: Tuple[float, float]):
        instance.height = int(size[1])

    def _update_bg(self, *args: Any):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _update_fade(self, *args: Any):
        self.fade_rect.size = (self.width, self.height * 0.3)  # type: ignore

    def _update_right_frame(self, instance: Widget, *args: Any):
        self.right_frame.pos = instance.pos  # type: ignore
        self.right_frame.size = instance.size  # type: ignore

    def _handle_complete(self, *args: Any):
        def delay_start(*args: Any, **kwargs: Any):
            self.on_complete()  # type: ignore

        if self.on_complete is not None:
            Clock.schedule_once(delay_start, 0.1)  # type: ignore

    @property
    def progress(self):
        return min(self.current_step / max(self.total_steps, 1), 1)

    def _update_ui(self, *args: Any) -> int:
        self.progress_bar.value = self.progress
        self.percentage_label.text = f"{int(self.progress * 100)}%"
        self.step_label.text = self.step_message

        if self.progress >= 1 and self.show_continue:
            self.continue_button.opacity = 1
            self.continue_button.disabled = False
        else:
            self.continue_button.opacity = 0
            self.continue_button.disabled = True

        return 1

    def next_step(self, message: Optional[str] = None):
        self.current_step += 1

        if message:
            self.step_message = message

        self._update_ui()

    def add_to_right_overlay(self, widget: Widget):
        self.right_content.add_widget(widget)

    def set_logo(self, source: str):
        self.logo_image.source = source

    def set_left_overlay_image(self, source: str):
        self.left_overlay.source = source
