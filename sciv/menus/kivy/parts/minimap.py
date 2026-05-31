from math import ceil, floor, hypot, sqrt
from typing import TYPE_CHECKING, Optional, cast

from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from panda3d.core import Point2, Point3

from helpers.tiles import Tiles
from managers.player import PlayerManager

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from system.camera import Camera
    from managers.world import World


class Minimap(FloatLayout, DirectObject):

    def __init__(self, **kwargs) -> None:
        self._base = kwargs.pop("base", None)
        super().__init__(**kwargs)
        DirectObject.__init__(self)

        self.size_hint = (None, None)
        self.pos_hint = {}

        self.frame_padding_px = float(dp(7))
        self.inner_padding_px = float(dp(5))
        self.header_height_px = float(dp(22))
        self.section_gap_px = float(dp(4))
        self.shadow_offset_px = float(dp(2))
        self.top_offset_px = float(dp(40))
        self.edge_margin_px = float(dp(12))
        self.min_map_px = float(dp(156))
        self.max_map_px = float(dp(238))
        self.map_size_ratio = 0.18
        self.border_width = 0.9
        self.city_marker_radius_px = float(dp(2.85))
        self.viewport_border_width = 0.95
        self.viewport_fill_alpha = 0.0
        self.viewport_line_alpha = 0.82
        self.zoom_levels = (1.0, 1.6, 2.4, 3.4, 5.0, 7.5, 11.0, 16.0)
        self._zoom_level_index = 0
        self._absolute_mode = False
        self.empire_border_alpha = 0.92
        self.empire_border_shadow_alpha = 0.34
        self.empire_border_inset_px = float(dp(1.0))
        self.empire_border_shorten_px = float(dp(0.65))

        self.world: Optional[World] = None
        self.camera: Optional[Camera] = None
        self.texture: Optional[Texture] = None
        self.display_texture: Optional[Texture] = None
        self.tiles: list[Tile] = []
        self.tiles_by_key: dict[tuple[int, int], Tile] = {}
        self._refresh_trigger = Clock.create_trigger(self._refresh_full_triggered, 0)
        self._overlay_trigger = Clock.create_trigger(self._refresh_overlay_triggered, 0)
        self._pending_texture_rebuild = False
        self._layout_scheduled = False
        self._is_registered = False
        self._last_window_size = self._get_window_size()
        self._window_poll_event = Clock.schedule_interval(self._poll_window_size, 0)
        self._drag_camera_active: Optional[bool] = None
        self._drag_camera_lock: Optional[bool] = None
        self._drag_zoom_enabled: Optional[bool] = None
        self._external_camera_capture = False

        self._columns = 0
        self._rows = 0
        self._world_min_x = 0.0
        self._world_max_x = 0.0
        self._world_min_y = 0.0
        self._world_max_y = 0.0
        self._world_width = 0.0
        self._world_height = 0.0
        self._world_step_x = 1.0
        self._world_step_y = 1.0
        self._hex_radius_world = 1.0
        self._hex_half_height_world = 1.0
        self._hex_radius_texture = 1.0
        self._hex_half_height_texture = 1.0
        self._view_center_x = 0.0
        self._view_center_y = 0.0
        self._view_min_x = 0.0
        self._view_max_x = 0.0
        self._view_min_y = 0.0
        self._view_max_y = 0.0
        self._view_width = 0.0
        self._view_height = 0.0
        self._texture_width = 0
        self._texture_height = 0
        self._display_region_key: Optional[tuple[int, int, int, int]] = None
        self._viewport_world_bounds: Optional[tuple[float, float, float, float]] = None
        self._viewport_world_polygon: Optional[list[tuple[float, float]]] = None
        self._last_camera_signature: Optional[tuple[float, ...]] = None
        self._map_slot_pos = (0.0, 0.0)
        self._map_slot_size = (0.0, 0.0)

        with self.canvas.before:
            self._shadow_color_instruction = Color(0.0, 0.0, 0.0, 0.30)
            self._shadow_rect = Rectangle()
            self._panel_color_instruction = Color(0.03, 0.035, 0.045, 0.97)
            self._panel_rect = Rectangle()
            self._header_color_instruction = Color(0.035, 0.04, 0.05, 0.99)
            self._header_rect = Rectangle()
            self._accent_color_instruction = Color(*self._get_accent_color(alpha=0.95))
            self._accent_rect = Rectangle()
            self._divider_color_instruction = Color(1.0, 1.0, 1.0, 0.035)
            self._divider_rect = Rectangle()
            self._slot_color_instruction = Color(0.01, 0.012, 0.018, 0.995)
            self._slot_rect = Rectangle()
            self._slot_border_color_instruction = Color(1.0, 1.0, 1.0, 0.055)
            self._slot_border = Line(rectangle=(0.0, 0.0, 0.0, 0.0), width=1.0)
            self._border_color_instruction = Color(0.09, 0.11, 0.145, 0.96)
            self._border_line = Line(rectangle=(0.0, 0.0, 0.0, 0.0), width=self.border_width)

        self.map_image = Image(allow_stretch=True, keep_ratio=True, size_hint=(None, None))
        self.map_image.color = (1.0, 1.0, 1.0, 0.99)
        self.add_widget(self.map_image)

        self.title_label = Label(
            text='[b]MINIMAP[/b]',
            markup=True,
            size_hint=(None, None),
            halign='left',
            valign='middle',
            font_size=dp(10.5),
            color=self._get_accent_color(alpha=1.0),
        )
        self.title_label.bind(size=self._bind_text_size)
        self.add_widget(self.title_label)

        self.meta_label = Label(
            text='',
            size_hint=(None, None),
            halign='right',
            valign='middle',
            font_size=dp(9),
            color=(0.72, 0.76, 0.83, 0.68),
        )
        self.meta_label.bind(size=self._bind_text_size)
        self.add_widget(self.meta_label)

        self.zoom_in_button = self._build_control_button(text='+', width=float(dp(20)), font_size=dp(11))
        self.zoom_in_button.bind(on_release=self._on_zoom_in_pressed)
        self.add_widget(self.zoom_in_button)

        self.zoom_out_button = self._build_control_button(text='−', width=float(dp(20)), font_size=dp(12))
        self.zoom_out_button.bind(on_release=self._on_zoom_out_pressed)
        self.add_widget(self.zoom_out_button)

        self.absolute_mode_button = self._build_control_button(text='ABS', width=float(dp(46)), font_size=dp(8))
        self.absolute_mode_button.bind(on_release=self._on_absolute_mode_pressed)
        self.add_widget(self.absolute_mode_button)

        self.overlay_instruction_group = self.canvas.after
        self._camera_poll_event = Clock.schedule_interval(self._poll_camera_state, 1 / 12.0)

        if Window is not None:
            Window.bind(size=self._on_window_resized)
        self.bind(size=self._on_layout_changed, pos=self._on_layout_changed)

        self._sync_widget_frame()
        self._update_panel_chrome()
        self._update_image_layout()

    def register(self) -> None:
        from managers.world import World
        from system.camera import Camera

        self.world = World.get_singleton_instance()
        self.camera = Camera.get_singleton_instance()

        if self._is_registered:
            self.refresh_full()
            return

        self.accept('game.gameplay.tiles.ownership_changed', self.schedule_full_refresh)
        self.accept('unit.action.found_city.success', self.schedule_full_refresh)
        self.accept('game.state.reset_start', self.schedule_full_refresh)
        self.accept('system.camera.zoom_ticked', self.schedule_overlay_refresh)
        self.accept('system.camera.zoom_ended', self.schedule_overlay_refresh)
        self._is_registered = True

        self.refresh_full()

    def destroy(self) -> None:
        if Window is not None:
            Window.unbind(size=self._on_window_resized)
        self.unbind(size=self._on_layout_changed, pos=self._on_layout_changed)
        self._window_poll_event.cancel()
        self._camera_poll_event.cancel()
        self._refresh_trigger.cancel()
        self._overlay_trigger.cancel()
        self._end_camera_capture()
        self.ignoreAll()
        self._is_registered = False

    def schedule_full_refresh(self, *_args) -> None:
        self._pending_texture_rebuild = True
        self._refresh_trigger()

    def schedule_overlay_refresh(self, *_args) -> None:
        self._overlay_trigger()

    def refresh_full(self) -> None:
        self._pending_texture_rebuild = True
        self._refresh_full_triggered(0.0)

    def _refresh_tile_cache(self) -> None:
        if self.world is None:
            self.tiles = []
            self.tiles_by_key = {}
            return

        self.tiles = list(self.world.get_grid().values())
        self.tiles_by_key = {(tile.x, tile.y): tile for tile in self.tiles}

    def refresh_overlays(self) -> None:
        self.overlay_instruction_group.clear()
        if self.world is None:
            return

        self._refresh_tile_cache()

        accent = self._get_accent_color(alpha=1.0)

        with self.overlay_instruction_group:
            self._draw_empire_borders()

            for tile in self.tiles:
                if tile.city is None:
                    continue

                owner = tile.city.player if tile.city is not None else (tile.get_owner() if tile.owner is not None else None)
                owner_color = self._coerce_color_tuple(owner.get_color() if owner is not None else None)
                canvas_pos = self._world_to_canvas(tile.pos_x, tile.pos_y)
                if canvas_pos is None:
                    continue

                marker_x, marker_y = canvas_pos
                shadow_diameter = self.city_marker_radius_px * 2.6
                marker_diameter = self.city_marker_radius_px * 2.0

                Color(0.0, 0.0, 0.0, 0.48)
                Ellipse(
                    pos=(
                        marker_x - shadow_diameter / 2.0,
                        marker_y - shadow_diameter / 2.0,
                    ),
                    size=(shadow_diameter, shadow_diameter),
                )

                Color(*owner_color[:3], 0.98)
                Ellipse(
                    pos=(
                        marker_x - marker_diameter / 2.0,
                        marker_y - marker_diameter / 2.0,
                    ),
                    size=(marker_diameter, marker_diameter),
                )

                Color(0.0, 0.0, 0.0, 0.55)
                Line(
                    ellipse=(
                        marker_x - marker_diameter / 2.0,
                        marker_y - marker_diameter / 2.0,
                        marker_diameter,
                        marker_diameter,
                    ),
                    width=0.8,
                )

            viewport_polygon = self._calculate_viewport_world_polygon()
            self._viewport_world_polygon = viewport_polygon
            self._viewport_world_bounds = self._polygon_bounds(viewport_polygon)
            if viewport_polygon is not None:
                clipped_polygon = self._clip_polygon_to_view(viewport_polygon)
                if len(clipped_polygon) >= 3:
                    canvas_points: list[float] = []
                    for point_x, point_y in clipped_polygon:
                        canvas_pos = self._world_to_canvas_raw(point_x, point_y)
                        if canvas_pos is None:
                            continue
                        canvas_points.extend([canvas_pos[0], canvas_pos[1]])

                    if len(canvas_points) >= 6:
                        outline_points = canvas_points + canvas_points[:2]
                        Color(0.0, 0.0, 0.0, 0.28)
                        Line(points=outline_points, width=self.viewport_border_width + 1.0)
                        Color(accent[0], accent[1], accent[2], self.viewport_line_alpha)
                        Line(points=outline_points, width=self.viewport_border_width)

            if self.camera is not None:
                pivot = self.camera.pivot.getPos()
                pivot_pos = self._world_to_canvas(float(pivot.getX()), float(pivot.getY()))
                if pivot_pos is not None:
                    radius = float(dp(3.5))
                    Color(0.0, 0.0, 0.0, 0.45)
                    Ellipse(
                        pos=(pivot_pos[0] - radius - 1.0, pivot_pos[1] - radius - 1.0),
                        size=((radius + 1.0) * 2.0, (radius + 1.0) * 2.0),
                    )
                    Color(accent[0], accent[1], accent[2], 0.98)
                    Ellipse(
                        pos=(pivot_pos[0] - radius, pivot_pos[1] - radius),
                        size=(radius * 2.0, radius * 2.0),
                    )

            self._draw_selected_tile_marker(accent)

    def _get_selected_tile(self) -> Optional[Tile]:
        ui_manager = getattr(self._base, 'ui_manager', None)
        if ui_manager is None:
            return None

        try:
            selected_tile = ui_manager.get_selected_tile()
        except Exception:
            return None

        if selected_tile is None or not hasattr(selected_tile, 'pos_x') or not hasattr(selected_tile, 'pos_y'):
            return None
        return cast(Tile, selected_tile)

    def _draw_selected_tile_marker(self, accent: tuple[float, float, float, float]) -> None:
        selected_tile = self._get_selected_tile()
        if selected_tile is None:
            return

        canvas_pos = self._world_to_canvas(selected_tile.pos_x, selected_tile.pos_y)
        if canvas_pos is None:
            return

        marker_x, marker_y = canvas_pos
        outer_radius = float(dp(4.1))
        inner_radius = float(dp(1.45))
        crosshair_radius = outer_radius + float(dp(1.3))

        Color(0.0, 0.0, 0.0, 0.58)
        Line(circle=(marker_x, marker_y, outer_radius + 0.9), width=1.8)

        Color(1.0, 0.97, 0.88, 0.96)
        Line(circle=(marker_x, marker_y, outer_radius), width=1.05)

        Color(accent[0], accent[1], accent[2], 0.92)
        Line(points=(marker_x - crosshair_radius, marker_y, marker_x + crosshair_radius, marker_y), width=0.9)
        Line(points=(marker_x, marker_y - crosshair_radius, marker_x, marker_y + crosshair_radius), width=0.9)

        Color(1.0, 1.0, 1.0, 0.98)
        Ellipse(
            pos=(marker_x - inner_radius, marker_y - inner_radius),
            size=(inner_radius * 2.0, inner_radius * 2.0),
        )

    def on_touch_down(self, touch):  # type: ignore[override]
        if super().on_touch_down(touch):
            return True

        if not self.collide_point(*touch.pos):
            return False

        button = getattr(touch, 'button', None)
        if button == 'scrollup':
            self._step_zoom(1)
            return True
        if button == 'scrolldown':
            self._step_zoom(-1)
            return True

        tile = self._tile_for_touch(touch.pos)
        if tile is None:
            return True

        touch.grab(self)
        touch.ud['minimap_dragging'] = True
        self._begin_camera_capture()
        self._focus_tile(tile)
        return True

    def on_touch_move(self, touch):  # type: ignore[override]
        if touch.grab_current is not self:
            return super().on_touch_move(touch)

        tile = self._tile_for_touch(touch.pos)
        if tile is not None:
            self._focus_tile(tile)
        return True

    def on_touch_up(self, touch):  # type: ignore[override]
        if touch.grab_current is self:
            touch.ungrab(self)
            self._end_camera_capture()
            return True
        return super().on_touch_up(touch)

    def _refresh_full_triggered(self, _dt: float) -> None:
        if self.world is None:
            return

        self._refresh_tile_cache()
        self._pending_texture_rebuild = True
        self._refresh_geometry(self.world)
        self._update_panel_chrome()
        self._update_image_layout()

        if self._pending_texture_rebuild:
            pixel_data = self._build_texture_bytes()
            if self._texture_width > 0 and self._texture_height > 0:
                if self.texture is None or self.texture.size != (self._texture_width, self._texture_height):
                    self.texture = Texture.create(size=(self._texture_width, self._texture_height), colorfmt='rgba')
                    self.texture.mag_filter = 'nearest'
                    self.texture.min_filter = 'nearest'
                self.texture.blit_buffer(pixel_data, colorfmt='rgba', bufferfmt='ubyte')
                self._display_region_key = None
            self._pending_texture_rebuild = False

        self._update_view_bounds(follow_camera=True)
        self._update_display_texture()

        self._refresh_overlay_triggered(0.0)

    def _refresh_overlay_triggered(self, _dt: float) -> None:
        self._update_view_bounds(follow_camera=True)
        self._update_panel_chrome()
        self._update_image_layout()
        self._update_display_texture()
        self.refresh_overlays()

    def _refresh_geometry(self, world: World) -> None:
        self._columns = world.cols
        self._rows = world.rows
        self.tiles = list(world.get_grid().values())
        self.tiles_by_key = {(tile.x, tile.y): tile for tile in self.tiles}

        if not self.tiles:
            self._world_min_x = 0.0
            self._world_max_x = 1.0
            self._world_min_y = 0.0
            self._world_max_y = 1.0
            self._world_width = 1.0
            self._world_height = 1.0
            self._world_step_x = 1.0
            self._world_step_y = 1.0
            self._hex_radius_world = 1.0
            self._hex_half_height_world = 1.0
            self._hex_radius_texture = 1.0
            self._hex_half_height_texture = 1.0
            self._view_center_x = 0.5
            self._view_center_y = 0.5
            self._view_min_x = 0.0
            self._view_max_x = 1.0
            self._view_min_y = 0.0
            self._view_max_y = 1.0
            self._view_width = 1.0
            self._view_height = 1.0
            self._texture_width = 1
            self._texture_height = 1
            return

        x_positions = [float(tile.pos_x) for tile in self.tiles]
        y_positions = [float(tile.pos_y) for tile in self.tiles]

        self._world_step_x = self._smallest_positive_step(x_positions) or 1.5
        self._world_step_y = self._smallest_positive_step(y_positions) or (sqrt(3) / 2.0)

        self._hex_radius_world = max(self._world_step_x / 1.5, 1e-6)
        self._hex_half_height_world = max(self._world_step_y, (sqrt(3) * self._hex_radius_world) / 2.0)

        self._world_min_x = min(x_positions) - self._hex_radius_world
        self._world_max_x = max(x_positions) + self._hex_radius_world
        self._world_min_y = min(y_positions) - self._hex_half_height_world
        self._world_max_y = max(y_positions) + self._hex_half_height_world
        self._world_width = max(self._world_max_x - self._world_min_x, self._world_step_x)
        self._world_height = max(self._world_max_y - self._world_min_y, self._world_step_y)

        desired_pixels_per_world_unit = 5.5
        desired_width = max(1, round(self._world_width * desired_pixels_per_world_unit))
        desired_height = max(1, round(self._world_height * desired_pixels_per_world_unit))
        largest_dimension = max(desired_width, desired_height)

        scale = 1.0
        min_dimension = 180
        max_dimension = 960
        if largest_dimension < min_dimension:
            scale *= min_dimension / largest_dimension
        if largest_dimension * scale > max_dimension:
            scale *= max_dimension / (largest_dimension * scale)

        self._texture_width = max(1, round(desired_width * scale))
        self._texture_height = max(1, round(desired_height * scale))
        self._hex_radius_texture = max(
            1.0,
            (self._hex_radius_world / max(self._world_width, 1e-6)) * max(self._texture_width - 1, 1),
        )
        self._hex_half_height_texture = max(
            1.0,
            (self._hex_half_height_world / max(self._world_height, 1e-6)) * max(self._texture_height - 1, 1),
        )

    def _build_texture_bytes(self) -> bytes:
        if self.world is None:
            return b''

        texture_width = max(1, self._texture_width)
        texture_height = max(1, self._texture_height)
        pixel_data = bytearray(texture_width * texture_height * 4)

        for y in range(texture_height):
            row_start = y * texture_width * 4
            for x in range(texture_width):
                pixel_data[row_start + x * 4: row_start + x * 4 + 4] = bytes((8, 11, 17, 255))

        for tile in self.tiles:
            tex_pos = self._world_to_texture_point(tile.pos_x, tile.pos_y)
            if tex_pos is None:
                continue

            rgba = self._tile_rgba(tile)
            outline_rgba = self._darken_rgba(rgba, 0.32)
            border_inset = max(0.85, min(self._hex_radius_texture, self._hex_half_height_texture) * 0.16)

            self._fill_hex(
                pixel_data,
                tex_pos[0],
                tex_pos[1],
                self._hex_radius_texture,
                self._hex_half_height_texture,
                outline_rgba,
            )
            self._fill_hex(
                pixel_data,
                tex_pos[0],
                tex_pos[1],
                max(0.55, self._hex_radius_texture - border_inset),
                max(0.55, self._hex_half_height_texture - border_inset * 0.9),
                rgba,
            )

        return bytes(pixel_data)

    def _tile_rgba(self, tile: Tile) -> tuple[int, int, int, int]:
        tile_color = self._coerce_color_tuple(tile.color())
        owner = getattr(tile, 'owner', None)
        if owner is not None:
            owner_color = self._coerce_color_tuple(owner.get_color())
            blend_ratio = 0.10
            red = tile_color[0] * (1.0 - blend_ratio) + owner_color[0] * blend_ratio
            green = tile_color[1] * (1.0 - blend_ratio) + owner_color[1] * blend_ratio
            blue = tile_color[2] * (1.0 - blend_ratio) + owner_color[2] * blend_ratio
        else:
            red, green, blue = tile_color[:3]

        return (
            round(max(0.0, min(1.0, red)) * 255),
            round(max(0.0, min(1.0, green)) * 255),
            round(max(0.0, min(1.0, blue)) * 255),
            255,
        )

    def _world_to_texture(self, world_x: float, world_y: float) -> Optional[tuple[int, int]]:
        texture_point = self._world_to_texture_point(world_x, world_y)
        if texture_point is None:
            return None
        return (round(texture_point[0]), round(texture_point[1]))

    def _world_to_texture_point(self, world_x: float, world_y: float) -> Optional[tuple[float, float]]:
        if self._texture_width <= 0 or self._texture_height <= 0:
            return None

        # Keep this normalization aligned with _world_to_canvas(), _canvas_to_world(),
        # and the texture row write order in _fill_polygon(). A mismatch in only one of
        # those stages can make the minimap look flipped or rotated even when it is using
        # the correct tile world coordinates.
        normalized_x = (float(world_x) - self._world_min_x) / max(self._world_width, 1e-6)
        normalized_y = (float(world_y) - self._world_min_y) / max(self._world_height, 1e-6)
        normalized_x = max(0.0, min(1.0, normalized_x))
        normalized_y = max(0.0, min(1.0, normalized_y))

        pixel_x = normalized_x * max(self._texture_width - 1, 1)
        pixel_y = normalized_y * max(self._texture_height - 1, 1)
        return (pixel_x, pixel_y)

    def _fill_hex(
        self,
        pixel_data: bytearray,
        center_x: float,
        center_y: float,
        radius_x: float,
        half_height: float,
        rgba: tuple[int, int, int, int],
    ) -> None:
        shoulder_x = radius_x * 0.5
        points = [
            (center_x + radius_x, center_y),
            (center_x + shoulder_x, center_y + half_height),
            (center_x - shoulder_x, center_y + half_height),
            (center_x - radius_x, center_y),
            (center_x - shoulder_x, center_y - half_height),
            (center_x + shoulder_x, center_y - half_height),
        ]
        self._fill_polygon(pixel_data, points, rgba)

    def _fill_polygon(
        self,
        pixel_data: bytearray,
        points: list[tuple[float, float]],
        rgba: tuple[int, int, int, int],
    ) -> None:
        if self._texture_width <= 0 or self._texture_height <= 0 or len(points) < 3:
            return

        fill_bytes = bytes(rgba)
        min_y = max(0, floor(min(y for _, y in points)))
        max_y = min(self._texture_height - 1, ceil(max(y for _, y in points)))
        if max_y < min_y:
            return

        for pixel_y in range(min_y, max_y + 1):
            scan_y = pixel_y + 0.5
            intersections: list[float] = []
            for index, (x1, y1) in enumerate(points):
                x2, y2 = points[(index + 1) % len(points)]
                if y1 == y2:
                    continue
                if (y1 <= scan_y < y2) or (y2 <= scan_y < y1):
                    ratio = (scan_y - y1) / (y2 - y1)
                    intersections.append(x1 + ratio * (x2 - x1))

            if len(intersections) < 2:
                continue

            intersections.sort()
            # pixel_y intentionally maps directly to the texture row here. Re-introducing
            # an inverted row write without updating the rest of the transform chain will
            # make the minimap appear mirrored against the live world.
            row_start = pixel_y * self._texture_width * 4
            for start_x, end_x in zip(intersections[0::2], intersections[1::2]):
                left = max(0, floor(min(start_x, end_x)))
                right = min(self._texture_width - 1, ceil(max(start_x, end_x)))
                for pixel_x in range(left, right + 1):
                    index = row_start + pixel_x * 4
                    pixel_data[index:index + 4] = fill_bytes

    def _darken_rgba(
        self,
        rgba: tuple[int, int, int, int],
        amount: float,
    ) -> tuple[int, int, int, int]:
        scale = max(0.0, min(1.0, 1.0 - amount))
        return (
            round(rgba[0] * scale),
            round(rgba[1] * scale),
            round(rgba[2] * scale),
            rgba[3],
        )

    def _world_to_canvas(self, world_x: float, world_y: float) -> Optional[tuple[float, float]]:
        if self._view_width <= 0 or self._view_height <= 0:
            return None

        # This helper must stay in the same orientation as _world_to_texture_point() and
        # _canvas_to_world(). Treat minimap bugs here as transform-chain bugs, not just as
        # isolated drawing glitches.
        draw_x, draw_y, draw_width, draw_height = self._image_draw_area()
        if draw_width <= 0 or draw_height <= 0:
            return None

        world_x = float(world_x)
        world_y = float(world_y)
        epsilon = 1e-6
        if (
            world_x < self._view_min_x - epsilon
            or world_x > self._view_max_x + epsilon
            or world_y < self._view_min_y - epsilon
            or world_y > self._view_max_y + epsilon
        ):
            return None

        normalized_x = (world_x - self._view_min_x) / max(self._view_width, 1e-6)
        normalized_y = (world_y - self._view_min_y) / max(self._view_height, 1e-6)

        canvas_x = draw_x + normalized_x * draw_width
        canvas_y = draw_y + normalized_y * draw_height
        return (canvas_x, canvas_y)

    def _canvas_to_world(self, canvas_x: float, canvas_y: float) -> Optional[tuple[float, float]]:
        draw_x, draw_y, draw_width, draw_height = self._image_draw_area()
        if draw_width <= 0 or draw_height <= 0:
            return None

        # Keep the inverse mapping in lockstep with _world_to_canvas(). Historical minimap
        # alignment bugs came from one stage flipping/normalizing differently than the rest.
        normalized_x = (canvas_x - draw_x) / draw_width
        normalized_y = (canvas_y - draw_y) / draw_height
        normalized_x = max(0.0, min(1.0, normalized_x))
        normalized_y = max(0.0, min(1.0, normalized_y))

        world_x = self._view_min_x + normalized_x * self._view_width
        world_y = self._view_min_y + normalized_y * self._view_height
        return (world_x, world_y)

    def _image_draw_area(self) -> tuple[float, float, float, float]:
        active_texture = self.map_image.texture
        if active_texture is None or active_texture.width <= 0 or active_texture.height <= 0:
            return (self.map_image.x, self.map_image.y, self.map_image.width, self.map_image.height)

        image_aspect = active_texture.width / active_texture.height
        box_width = self.map_image.width
        box_height = self.map_image.height
        box_aspect = box_width / box_height if box_height > 0 else image_aspect

        if box_aspect > image_aspect:
            draw_height = box_height
            draw_width = draw_height * image_aspect
        else:
            draw_width = box_width
            draw_height = draw_width / image_aspect

        draw_x = self.map_image.x + (box_width - draw_width) / 2.0
        draw_y = self.map_image.y + (box_height - draw_height) / 2.0
        return (draw_x, draw_y, draw_width, draw_height)

    def _tile_for_touch(self, position: tuple[float, float]) -> Optional[Tile]:
        world_pos = self._canvas_to_world(*position)
        if world_pos is None or self.world is None:
            return None
        return self._nearest_tile_for_world(*world_pos)

    def _nearest_tile_for_world(self, world_x: float, world_y: float) -> Optional[Tile]:
        if self.world is None:
            return None

        if not self.tiles:
            self._refresh_tile_cache()

        if not self.tiles:
            return None

        candidates = self.tiles

        best_tile: Optional[Tile] = None
        best_distance = float('inf')
        for tile in candidates:
            distance = hypot(float(tile.pos_x) - world_x, float(tile.pos_y) - world_y)
            if distance < best_distance:
                best_distance = distance
                best_tile = tile

        return best_tile

    def _focus_tile(self, tile: Tile) -> None:
        if tile is None:
            return
        self._view_center_x = float(tile.pos_x)
        self._view_center_y = float(tile.pos_y)
        messenger.send('game.camera.request.center_on_tile', [tile])
        self.schedule_overlay_refresh()

    def _calculate_viewport_world_polygon(self) -> Optional[list[tuple[float, float]]]:
        if self.camera is None:
            return None

        lens = self.camera.get_lens()
        camera_node = self.camera.base_camera()
        world_root = self.camera.base.render
        target_plane_z = float(self.camera.pivot.getPos(world_root).getZ())
        corners = (Point2(-1.0, -1.0), Point2(1.0, -1.0), Point2(1.0, 1.0), Point2(-1.0, 1.0))
        intersections: list[tuple[float, float]] = []

        for corner in corners:
            near = Point3()
            far = Point3()
            if not lens.extrude(corner, near, far):
                continue

            near_world = world_root.getRelativePoint(camera_node, near)
            far_world = world_root.getRelativePoint(camera_node, far)
            direction = far_world - near_world
            if abs(direction.getZ()) < 1e-6:
                continue

            t = (target_plane_z - near_world.getZ()) / direction.getZ()
            if t < 0.0:
                continue
            intersection = near_world + (direction * t)
            clamped_x = min(max(float(intersection.getX()), self._world_min_x), self._world_max_x)
            clamped_y = min(max(float(intersection.getY()), self._world_min_y), self._world_max_y)
            intersections.append((clamped_x, clamped_y))

        if len(intersections) < 3:
            return None

        return intersections

    def _polygon_bounds(
        self,
        polygon: Optional[list[tuple[float, float]]],
    ) -> Optional[tuple[float, float, float, float]]:
        if polygon is None or len(polygon) < 3:
            return None

        min_x = min(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        max_x = max(point[0] for point in polygon)
        max_y = max(point[1] for point in polygon)
        if min_x >= max_x or min_y >= max_y:
            return None
        return (min_x, min_y, max_x, max_y)

    def _polygon_centroid(
        self,
        polygon: Optional[list[tuple[float, float]]],
    ) -> Optional[tuple[float, float]]:
        if polygon is None or len(polygon) < 3:
            return None

        signed_area = 0.0
        centroid_x = 0.0
        centroid_y = 0.0

        for current, nxt in zip(polygon, polygon[1:] + polygon[:1]):
            cross = current[0] * nxt[1] - nxt[0] * current[1]
            signed_area += cross
            centroid_x += (current[0] + nxt[0]) * cross
            centroid_y += (current[1] + nxt[1]) * cross

        if abs(signed_area) < 1e-6:
            average_x = sum(point[0] for point in polygon) / len(polygon)
            average_y = sum(point[1] for point in polygon) / len(polygon)
            return (average_x, average_y)

        scale = 1.0 / (3.0 * signed_area)
        return (centroid_x * scale, centroid_y * scale)

    def _begin_camera_capture(self) -> None:
        if self.camera is None or self._external_camera_capture:
            return

        self._drag_camera_active = bool(getattr(self.camera, 'active', True))
        self._drag_camera_lock = bool(getattr(self.camera, 'lock', False))
        self._drag_zoom_enabled = bool(getattr(self.camera, 'zoom_enabled', True))
        self.camera.begin_external_capture()
        self._external_camera_capture = True

    def _end_camera_capture(self) -> None:
        if self.camera is None or not self._external_camera_capture:
            return

        self.camera.end_external_capture(
            active=self._drag_camera_active if self._drag_camera_active is not None else True,
            lock=self._drag_camera_lock,
            zoom_enabled=self._drag_zoom_enabled,
        )
        self._drag_camera_active = None
        self._drag_camera_lock = None
        self._drag_zoom_enabled = None
        self._external_camera_capture = False

    def _on_window_resized(self, *_args) -> None:
        self._schedule_layout_refresh()

    def _poll_window_size(self, _dt: float) -> None:
        size = self._get_window_size()
        if size != self._last_window_size:
            self._last_window_size = size
            self._schedule_layout_refresh()

    def _poll_camera_state(self, _dt: float) -> None:
        signature = self._get_camera_signature()
        if signature is None:
            return

        if self._last_camera_signature is None:
            self._last_camera_signature = signature
            self.schedule_overlay_refresh()
            return

        if signature != self._last_camera_signature:
            self._last_camera_signature = signature
            self.schedule_overlay_refresh()

    def _build_control_button(self, text: str, width: float, font_size: float = None) -> Button:
        button = Button(
            text=text,
            size_hint=(None, None),
            width=width,
            height=float(dp(18)),
            font_size=font_size if font_size is not None else dp(10),
            background_normal='',
            background_down='',
            background_disabled_normal='',
            border=(0, 0, 0, 0),
            bold=True,
        )
        return button

    def _on_zoom_in_pressed(self, *_args) -> None:
        self._step_zoom(1)

    def _on_zoom_out_pressed(self, *_args) -> None:
        self._step_zoom(-1)

    def _on_absolute_mode_pressed(self, *_args) -> None:
        self._absolute_mode = not self._absolute_mode
        self.schedule_overlay_refresh()

    def _current_zoom_factor(self) -> float:
        if self._absolute_mode:
            return 1.0
        return self.zoom_levels[self._zoom_level_index]

    def _step_zoom(self, direction: int) -> None:
        if self._absolute_mode:
            return
        new_index = max(0, min(len(self.zoom_levels) - 1, self._zoom_level_index + direction))
        if new_index == self._zoom_level_index:
            return
        self._zoom_level_index = new_index
        self.schedule_overlay_refresh()

    def _get_camera_signature(self) -> Optional[tuple[float, ...]]:
        if self.camera is None:
            return None

        try:
            pivot = self.camera.pivot.getPos()
            camera_pos = self.camera.getPos()
            camera_hpr = self.camera.getHpr()
            return (
                round(float(pivot.getX()), 2),
                round(float(pivot.getY()), 2),
                round(float(camera_pos.getX()), 2),
                round(float(camera_pos.getY()), 2),
                round(float(camera_pos.getZ()), 2),
                round(float(camera_hpr.getX()), 1),
                round(float(camera_hpr.getY()), 1),
                round(float(getattr(self.camera, 'zoom', 0.0)), 2),
            )
        except Exception:
            return None

    def _get_camera_pivot_world(self) -> Optional[tuple[float, float]]:
        if self.camera is None:
            return None

        try:
            pivot = self.camera.pivot.getPos()
            return (float(pivot.getX()), float(pivot.getY()))
        except Exception:
            return None

    def _update_view_bounds(self, *, follow_camera: bool = False) -> None:
        if self._world_width <= 0 or self._world_height <= 0:
            return

        center_x = self._view_center_x if self._view_width > 0 else (self._world_min_x + self._world_max_x) / 2.0
        center_y = self._view_center_y if self._view_height > 0 else (self._world_min_y + self._world_max_y) / 2.0

        if follow_camera:
            viewport_polygon = self._calculate_viewport_world_polygon()
            viewport_center = self._polygon_centroid(viewport_polygon)
            if viewport_center is not None:
                center_x, center_y = viewport_center
            else:
                camera_pivot = self._get_camera_pivot_world()
                if camera_pivot is not None:
                    center_x, center_y = camera_pivot

        zoom_factor = max(1.0, self._current_zoom_factor())
        self._view_width = self._world_width / zoom_factor
        self._view_height = self._world_height / zoom_factor

        half_width = self._view_width / 2.0
        half_height = self._view_height / 2.0

        if self._view_width >= self._world_width:
            center_x = (self._world_min_x + self._world_max_x) / 2.0
        else:
            center_x = min(max(center_x, self._world_min_x + half_width), self._world_max_x - half_width)

        if self._view_height >= self._world_height:
            center_y = (self._world_min_y + self._world_max_y) / 2.0
        else:
            center_y = min(max(center_y, self._world_min_y + half_height), self._world_max_y - half_height)

        self._view_center_x = center_x
        self._view_center_y = center_y
        self._view_min_x = center_x - half_width
        self._view_max_x = center_x + half_width
        self._view_min_y = center_y - half_height
        self._view_max_y = center_y + half_height

    def _update_display_texture(self) -> None:
        if self.texture is None or self._texture_width <= 0 or self._texture_height <= 0:
            return

        if self._current_zoom_factor() <= 1.0 + 1e-6:
            self._display_region_key = None
            self.display_texture = self.texture
            self.map_image.texture = self.texture
            return

        left = ((self._view_min_x - self._world_min_x) / max(self._world_width, 1e-6)) * max(self._texture_width - 1, 1)
        right = ((self._view_max_x - self._world_min_x) / max(self._world_width, 1e-6)) * max(self._texture_width - 1, 1)
        bottom = ((self._view_min_y - self._world_min_y) / max(self._world_height, 1e-6)) * max(
            self._texture_height - 1, 1
        )
        top = ((self._view_max_y - self._world_min_y) / max(self._world_height, 1e-6)) * max(
            self._texture_height - 1, 1
        )

        region_x = max(0, floor(min(left, right)))
        region_y = max(0, floor(min(bottom, top)))
        region_right = min(self._texture_width, ceil(max(left, right)) + 1)
        region_top = min(self._texture_height, ceil(max(bottom, top)) + 1)
        region_width = max(1, region_right - region_x)
        region_height = max(1, region_top - region_y)
        region_key = (region_x, region_y, region_width, region_height)

        if self._display_region_key == region_key and self.display_texture is not None:
            self.map_image.texture = self.display_texture
            return

        self._display_region_key = region_key
        self.display_texture = self.texture.get_region(region_x, region_y, region_width, region_height)
        self.display_texture.mag_filter = 'nearest'
        self.display_texture.min_filter = 'nearest'
        self.map_image.texture = self.display_texture

    def _clip_bounds_to_view(
        self,
        bounds: tuple[float, float, float, float],
    ) -> Optional[tuple[float, float, float, float]]:
        min_x = max(bounds[0], self._view_min_x)
        min_y = max(bounds[1], self._view_min_y)
        max_x = min(bounds[2], self._view_max_x)
        max_y = min(bounds[3], self._view_max_y)
        if min_x >= max_x or min_y >= max_y:
            return None
        return (min_x, min_y, max_x, max_y)

    def _clip_polygon_to_view(
        self,
        polygon: list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        if not polygon:
            return []

        clipped = polygon
        clipped = self._clip_polygon_against_vertical(clipped, self._view_min_x, keep_greater=True)
        clipped = self._clip_polygon_against_vertical(clipped, self._view_max_x, keep_greater=False)
        clipped = self._clip_polygon_against_horizontal(clipped, self._view_min_y, keep_greater=True)
        clipped = self._clip_polygon_against_horizontal(clipped, self._view_max_y, keep_greater=False)
        return clipped

    def _clip_polygon_against_vertical(
        self,
        polygon: list[tuple[float, float]],
        boundary_x: float,
        *,
        keep_greater: bool,
    ) -> list[tuple[float, float]]:
        if not polygon:
            return []

        clipped: list[tuple[float, float]] = []
        for current, nxt in zip(polygon, polygon[1:] + polygon[:1]):
            current_inside = current[0] >= boundary_x if keep_greater else current[0] <= boundary_x
            next_inside = nxt[0] >= boundary_x if keep_greater else nxt[0] <= boundary_x

            if current_inside and next_inside:
                clipped.append(nxt)
            elif current_inside and not next_inside:
                clipped.append(self._intersect_vertical(current, nxt, boundary_x))
            elif not current_inside and next_inside:
                clipped.append(self._intersect_vertical(current, nxt, boundary_x))
                clipped.append(nxt)

        return clipped

    def _clip_polygon_against_horizontal(
        self,
        polygon: list[tuple[float, float]],
        boundary_y: float,
        *,
        keep_greater: bool,
    ) -> list[tuple[float, float]]:
        if not polygon:
            return []

        clipped: list[tuple[float, float]] = []
        for current, nxt in zip(polygon, polygon[1:] + polygon[:1]):
            current_inside = current[1] >= boundary_y if keep_greater else current[1] <= boundary_y
            next_inside = nxt[1] >= boundary_y if keep_greater else nxt[1] <= boundary_y

            if current_inside and next_inside:
                clipped.append(nxt)
            elif current_inside and not next_inside:
                clipped.append(self._intersect_horizontal(current, nxt, boundary_y))
            elif not current_inside and next_inside:
                clipped.append(self._intersect_horizontal(current, nxt, boundary_y))
                clipped.append(nxt)

        return clipped

    def _intersect_vertical(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        boundary_x: float,
    ) -> tuple[float, float]:
        delta_x = end[0] - start[0]
        if abs(delta_x) < 1e-6:
            return (boundary_x, start[1])
        ratio = (boundary_x - start[0]) / delta_x
        return (boundary_x, start[1] + (end[1] - start[1]) * ratio)

    def _intersect_horizontal(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        boundary_y: float,
    ) -> tuple[float, float]:
        delta_y = end[1] - start[1]
        if abs(delta_y) < 1e-6:
            return (start[0], boundary_y)
        ratio = (boundary_y - start[1]) / delta_y
        return (start[0] + (end[0] - start[0]) * ratio, boundary_y)

    def _draw_empire_borders(self) -> None:
        if self._view_width <= 0 or self._view_height <= 0:
            return

        line_width = max(1.0, min(1.8, 1.0 + (self._current_zoom_factor() - 1.0) * 0.22))
        shadow_width = line_width + 1.0

        for tile in self.tiles:
            owner = self._get_empire_owner(tile)
            if owner is None:
                continue
            if not self._tile_intersects_view(tile):
                continue

            center = self._world_to_canvas_raw(float(tile.pos_x), float(tile.pos_y))
            if center is None:
                continue

            vertices = self._hex_canvas_vertices(center[0], center[1])
            if len(vertices) != 6:
                continue

            owner_color = self._coerce_color_tuple(owner.get_color())
            neighbor_offsets = Tiles.get_directions_per_col(tile.x)
            segment_indices = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0))

            for edge_index, (dx, dy) in enumerate(neighbor_offsets):
                neighbor = self.tiles_by_key.get((tile.x + dx, tile.y + dy))
                neighbor_owner = self._get_empire_owner(neighbor)
                if neighbor_owner is owner:
                    continue

                start_index, end_index = segment_indices[edge_index]
                start = vertices[start_index]
                end = vertices[end_index]
                inset_start, inset_end = self._inset_segment_toward_center(start, end, center)

                Color(0.0, 0.0, 0.0, self.empire_border_shadow_alpha)
                Line(points=[inset_start[0], inset_start[1], inset_end[0], inset_end[1]], width=shadow_width)
                Color(owner_color[0], owner_color[1], owner_color[2], self.empire_border_alpha)
                Line(points=[inset_start[0], inset_start[1], inset_end[0], inset_end[1]], width=line_width)

    def _get_empire_owner(self, tile: Optional[Tile]):
        if tile is None:
            return None

        owner = getattr(tile, 'owner', None)
        if owner is None:
            return None
        if getattr(owner, 'is_nature', False):
            return None
        if getattr(owner, 'is_barbarian', False):
            return None
        return owner

    def _tile_intersects_view(self, tile: Tile) -> bool:
        world_x = float(tile.pos_x)
        world_y = float(tile.pos_y)
        return not (
            world_x + self._hex_radius_world < self._view_min_x
            or world_x - self._hex_radius_world > self._view_max_x
            or world_y + self._hex_half_height_world < self._view_min_y
            or world_y - self._hex_half_height_world > self._view_max_y
        )

    def _world_to_canvas_raw(self, world_x: float, world_y: float) -> Optional[tuple[float, float]]:
        if self._view_width <= 0 or self._view_height <= 0:
            return None

        draw_x, draw_y, draw_width, draw_height = self._image_draw_area()
        if draw_width <= 0 or draw_height <= 0:
            return None

        normalized_x = (float(world_x) - self._view_min_x) / max(self._view_width, 1e-6)
        normalized_y = (float(world_y) - self._view_min_y) / max(self._view_height, 1e-6)
        canvas_x = draw_x + normalized_x * draw_width
        canvas_y = draw_y + normalized_y * draw_height
        return (canvas_x, canvas_y)

    def _hex_canvas_vertices(self, center_x: float, center_y: float) -> list[tuple[float, float]]:
        draw_x, draw_y, draw_width, draw_height = self._image_draw_area()
        if draw_width <= 0 or draw_height <= 0:
            return []

        radius_x = (self._hex_radius_world / max(self._view_width, 1e-6)) * draw_width
        half_height = (self._hex_half_height_world / max(self._view_height, 1e-6)) * draw_height
        shoulder_x = radius_x * 0.5
        return [
            (center_x + radius_x, center_y),
            (center_x + shoulder_x, center_y + half_height),
            (center_x - shoulder_x, center_y + half_height),
            (center_x - radius_x, center_y),
            (center_x - shoulder_x, center_y - half_height),
            (center_x + shoulder_x, center_y - half_height),
        ]

    def _inset_segment_toward_center(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        center: tuple[float, float],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        mid_x = (start[0] + end[0]) * 0.5
        mid_y = (start[1] + end[1]) * 0.5
        to_center_x = center[0] - mid_x
        to_center_y = center[1] - mid_y
        to_center_length = hypot(to_center_x, to_center_y)

        inset_x = 0.0
        inset_y = 0.0
        if to_center_length > 1e-6:
            inset_scale = self.empire_border_inset_px / to_center_length
            inset_x = to_center_x * inset_scale
            inset_y = to_center_y * inset_scale

        tangent_x = end[0] - start[0]
        tangent_y = end[1] - start[1]
        tangent_length = hypot(tangent_x, tangent_y)
        shorten_x = 0.0
        shorten_y = 0.0
        if tangent_length > 1e-6:
            shorten_scale = min(self.empire_border_shorten_px, tangent_length * 0.18) / tangent_length
            shorten_x = tangent_x * shorten_scale
            shorten_y = tangent_y * shorten_scale

        return (
            (start[0] + inset_x + shorten_x, start[1] + inset_y + shorten_y),
            (end[0] + inset_x - shorten_x, end[1] + inset_y - shorten_y),
        )

    def _get_window_size(self) -> tuple[float, float]:
        if self._base is not None and getattr(self._base, "win", None) is not None:
            try:
                width = float(self._base.win.getXSize())  # type: ignore[attr-defined]
                height = float(self._base.win.getYSize())  # type: ignore[attr-defined]
                if width > 0 and height > 0:
                    return (width, height)
            except Exception:
                pass

        if Window is not None:
            try:
                width = float(Window.width)
                height = float(Window.height)
                if width > 0 and height > 0:
                    return (width, height)
            except Exception:
                pass

        fallback_width = float(self.width) if self.width > 0 else 1.0
        fallback_height = float(self.height) if self.height > 0 else 1.0
        return (fallback_width, fallback_height)

    def _on_layout_changed(self, *_args) -> None:
        self._update_panel_chrome()
        self._update_image_layout()
        self.schedule_overlay_refresh()

    def _schedule_layout_refresh(self) -> None:
        if self._layout_scheduled:
            return
        self._layout_scheduled = True
        Clock.schedule_once(self._refresh_layout, 0)

    def _refresh_layout(self, _dt: float) -> None:
        self._layout_scheduled = False
        self._sync_widget_frame()
        self._update_panel_chrome()
        self._update_image_layout()
        self.schedule_overlay_refresh()

    def _sync_widget_frame(self) -> None:
        window_width, window_height = self._get_window_size()
        target_map_size = max(
            self.min_map_px,
            min(self.max_map_px, min(window_width, window_height) * self.map_size_ratio),
        )

        target_width = target_map_size + self.frame_padding_px * 2.0
        target_height = (
            target_map_size
            + self.header_height_px
            + self.section_gap_px
            + self.frame_padding_px * 2.0
        )

        target_x = window_width - target_width - self.edge_margin_px
        target_y = window_height - target_height - self.top_offset_px

        if (
            abs(self.width - target_width) > 0.5
            or abs(self.height - target_height) > 0.5
        ):
            self.size = (target_width, target_height)

        if (
            abs(self.x - target_x) > 0.5
            or abs(self.y - target_y) > 0.5
        ):
            self.pos = (target_x, target_y)

    def _update_panel_chrome(self) -> None:
        accent = self._get_accent_color(alpha=1.0)
        muted = (0.72, 0.76, 0.83, 0.68)

        self._shadow_rect.pos = (self.x + self.shadow_offset_px, self.y - self.shadow_offset_px)
        self._shadow_rect.size = self.size
        self._panel_rect.pos = self.pos
        self._panel_rect.size = self.size

        header_x = self.x + self.frame_padding_px
        header_y = self.y + self.height - self.frame_padding_px - self.header_height_px
        header_width = max(0.0, self.width - self.frame_padding_px * 2.0)
        header_height = self.header_height_px

        self._header_rect.pos = (header_x, header_y)
        self._header_rect.size = (header_width, header_height)
        self._accent_color_instruction.rgba = accent
        self._accent_rect.pos = (header_x, header_y + header_height - float(dp(1.5)))
        self._accent_rect.size = (header_width, float(dp(1.5)))
        self._divider_rect.pos = (header_x, header_y)
        self._divider_rect.size = (header_width, 1.0)

        slot_x = self.x + self.frame_padding_px
        slot_y = self.y + self.frame_padding_px
        slot_width = max(0.0, self.width - self.frame_padding_px * 2.0)
        slot_height = max(
            0.0,
            self.height - self.frame_padding_px * 2.0 - self.header_height_px - self.section_gap_px,
        )
        self._map_slot_pos = (slot_x, slot_y)
        self._map_slot_size = (slot_width, slot_height)

        self._slot_rect.pos = self._map_slot_pos
        self._slot_rect.size = self._map_slot_size
        self._slot_border.rectangle = (slot_x, slot_y, slot_width, slot_height)
        self._border_line.rectangle = (self.x, self.y, self.width, self.height)

        title_padding = float(dp(6))
        meta_width = max(float(dp(74)), min(float(dp(104)), header_width * 0.42))
        title_width = max(0.0, header_width - meta_width - title_padding * 2.0)

        self.title_label.color = accent
        self.title_label.size = (title_width, header_height)
        self.title_label.pos = (header_x + title_padding, header_y)

        self.meta_label.color = muted
        if self._columns > 0 and self._rows > 0:
            zoom_label = 'ABS' if self._absolute_mode else f'{self._current_zoom_factor():g}×'
            self.meta_label.text = f'{self._columns}×{self._rows} • {zoom_label}'
        else:
            self.meta_label.text = ''
        self.meta_label.size = (meta_width, header_height)
        self.meta_label.pos = (header_x + header_width - meta_width - title_padding, header_y)

    def _update_image_layout(self) -> None:
        slot_x, slot_y = self._map_slot_pos
        slot_width, slot_height = self._map_slot_size
        available_width = max(0.0, slot_width - self.inner_padding_px * 2.0)
        available_height = max(0.0, slot_height - self.inner_padding_px * 2.0)

        self.map_image.size = (available_width, available_height)
        self.map_image.pos = (slot_x + self.inner_padding_px, slot_y + self.inner_padding_px)
        self._update_control_buttons()

    def _update_control_buttons(self) -> None:
        inset = float(dp(6))
        spacing = float(dp(4))
        small_width = float(dp(20))
        small_height = float(dp(18))
        abs_width = float(dp(46)) if self._absolute_mode else float(dp(32))
        abs_height = float(dp(18))

        right_edge = self.map_image.x + self.map_image.width - inset
        top_edge = self.map_image.y + self.map_image.height - inset

        self.zoom_out_button.size = (small_width, small_height)
        self.zoom_out_button.pos = (
            right_edge - small_width * 2 - spacing,
            top_edge - small_height,
        )

        self.zoom_in_button.size = (small_width, small_height)
        self.zoom_in_button.pos = (
            right_edge - small_width,
            top_edge - small_height,
        )

        self.absolute_mode_button.size = (abs_width, abs_height)
        self.absolute_mode_button.pos = (
            self.zoom_out_button.x - spacing - abs_width,
            top_edge - abs_height,
        )

        accent = self._get_accent_color(alpha=1.0)
        neutral_bg = (0.065, 0.078, 0.108, 0.94)
        disabled_bg = (0.04, 0.05, 0.072, 0.86)
        text_normal = (0.90, 0.93, 0.97, 0.98)
        text_disabled = (0.46, 0.51, 0.60, 0.88)
        active_bg = (
            min(1.0, accent[0] * 0.62),
            min(1.0, accent[1] * 0.62),
            min(1.0, accent[2] * 0.62),
            0.95,
        )

        zoom_in_disabled = self._absolute_mode or self._zoom_level_index >= len(self.zoom_levels) - 1
        zoom_out_disabled = self._absolute_mode or self._zoom_level_index <= 0

        self.zoom_in_button.disabled = zoom_in_disabled
        self.zoom_out_button.disabled = zoom_out_disabled

        self.zoom_in_button.background_color = disabled_bg if zoom_in_disabled else neutral_bg
        self.zoom_out_button.background_color = disabled_bg if zoom_out_disabled else neutral_bg
        self.absolute_mode_button.background_color = active_bg if self._absolute_mode else neutral_bg

        self.zoom_in_button.color = text_disabled if zoom_in_disabled else text_normal
        self.zoom_out_button.color = text_disabled if zoom_out_disabled else text_normal
        self.absolute_mode_button.color = text_normal
        self.absolute_mode_button.text = 'ABS ON' if self._absolute_mode else 'ABS'

    def _bind_text_size(self, instance, value) -> None:
        instance.text_size = cast(tuple[float, float], value)

    def _smallest_positive_step(self, values: list[float]) -> float:
        unique_values = sorted(set(values))
        smallest = float('inf')
        for first, second in zip(unique_values, unique_values[1:]):
            difference = second - first
            if difference > 1e-4 and difference < smallest:
                smallest = difference
        return 1.0 if smallest == float('inf') else smallest

    def _coerce_color_tuple(self, color_value) -> tuple[float, float, float, float]:
        if isinstance(color_value, (tuple, list)):
            red = float(color_value[0]) if len(color_value) > 0 else 1.0
            green = float(color_value[1]) if len(color_value) > 1 else red
            blue = float(color_value[2]) if len(color_value) > 2 else green
            alpha = float(color_value[3]) if len(color_value) > 3 else 1.0
            return (red, green, blue, alpha)
        return (1.0, 1.0, 1.0, 1.0)

    def _get_accent_color(self, alpha: float = 1.0) -> tuple[float, float, float, float]:
        fallback = (0.82, 0.86, 0.92, alpha)
        try:
            player = PlayerManager.session_player()
            base = self._coerce_color_tuple(player.get_color())
            return (
                min(1.0, base[0] * 0.78 + 0.22),
                min(1.0, base[1] * 0.78 + 0.22),
                min(1.0, base[2] * 0.78 + 0.22),
                alpha,
            )
        except Exception:
            return fallback
