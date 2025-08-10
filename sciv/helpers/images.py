from typing import Iterable, List, Optional, Tuple

import PIL.Image
from helpers.colors import Tuple4f
from kivy.graphics.texture import Texture as KivyTexture
from kivy.uix.image import Image as KivyImage
from panda3d.core import SamplerState, Texture
from PIL import Image, ImageDraw, ImageFont


def generate_city_nameplate(
    left_img: Image.Image,
    middle_img: Image.Image,
    right_img: Image.Image,
    city_name: str,
    is_capital: bool,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    padding: Tuple[int, int] = (10, 5),
    text_offset_y: int = 0,
    star_img: Optional[Image.Image] = None,
    star_offset_y: int = 0,
    star_offset_x: int = 0,
    text_color: Tuple4f = (0, 0, 0, 255),
) -> Image.Image:
    draw = ImageDraw.Draw(middle_img)

    # Load text
    text = city_name

    # Measure text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Star size if needed
    star_width = star_img.width if (is_capital and star_img is not None) else 0
    star_padding = 10 if star_width > 0 else 0  # padding between star and text

    # Total width = star + gap + text
    content_width = text_width + star_width + star_padding

    # Total image width = left + middle + right
    total_width: int = int(left_img.width + content_width + 2 * padding[0] + right_img.width)
    total_height: int = max(left_img.height, middle_img.height, right_img.height)

    # Create final plate
    final_img = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    # Paste parts
    final_img.paste(left_img, (0, (total_height - left_img.height) // 2))
    middle_width = int(content_width + 2 * padding[0])
    stretched_middle = middle_img.resize((middle_width, middle_img.height))
    final_img.paste(stretched_middle, (left_img.width, (total_height - middle_img.height) // 2))
    final_img.paste(right_img, (left_img.width + middle_width, (total_height - right_img.height) // 2))

    # Draw
    text_x = left_img.width + padding[0] + (star_width + star_padding)
    text_y = (total_height - text_height) // 2 - text_offset_y

    draw = ImageDraw.Draw(final_img)

    if is_capital and star_img is not None:
        star_y = (total_height - star_img.height) // 2 - text_offset_y
        final_img.paste(star_img, (left_img.width + padding[0] + star_offset_x, star_y + star_offset_y), star_img)

    draw.text((text_x, text_y), text, font=font, fill=text_color)  # type: ignore

    return final_img


def draw_text_on_image(
    base_image: Image.Image | str,
    text_entries: list[tuple[str, tuple[int, int]]],
    font_path: str | ImageFont.FreeTypeFont,
    font_size: int = 16,
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    save: bool = False,
    save_path: str = "output_image.png",
    outline: bool = True,
    outline_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    outline_width: int = 1,
) -> bool:
    if isinstance(base_image, str):
        base_image = Image.open(base_image).convert("RGBA")

    if isinstance(font_path, str):
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = font_path

    text_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    outline_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))

    draw_outline = ImageDraw.Draw(outline_layer)
    draw_text = ImageDraw.Draw(text_layer)

    for text, position in text_entries:
        x, y = position

        if outline:
            # Draw the outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw_outline.text((x + dx, y + dy), text, font=font, fill=outline_color)

        # Draw the main text on text layer
        draw_text.text(position, text, font=font, fill=text_color)

    # First combine the outline and text layers
    combined = Image.alpha_composite(outline_layer, text_layer)

    # Composite final onto base image
    base_image = Image.alpha_composite(base_image, combined)

    if save:
        base_image.save(save_path)

    return True


def create_stacked_horizontal_images(images: List[Image.Image], offset: Tuple[int, int] = (10, 0)) -> Image.Image:
    """
    Stack images horizontally with true layering: earlier images appear behind later ones.

    :param images: List of PIL Image objects to stack.
    :param offset: Tuple (x_offset, y_offset) for each subsequent image.
    :return: Combined PIL Image with stacked layout.
    """
    if not images:
        raise ValueError("No images provided")

    img_width, img_height = images[0].size
    x_off, y_off = offset
    total_width = img_width + x_off * (len(images) - 1)
    total_height = img_height + y_off * (len(images) - 1)
    composite = PIL.Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    composite = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    for i, img in enumerate(images):
        # Compute position relative to reverse stacking
        pos = (i * x_off, i * y_off)
        composite.alpha_composite(img, dest=pos)

    return composite


def pil_image_to_panda3d_texture(pil_img: Image.Image) -> Texture:
    """Convert a PIL Image (RGBA) to a Panda3D Texture directly in memory."""
    pil_img = pil_img.convert("RGBA")

    # --- Swap R and B to fix Panda3D's channel order expectation ---
    r, g, b, a = pil_img.split()
    pil_img = Image.merge("RGBA", (b, g, r, a))

    width, height = pil_img.size
    raw_data = pil_img.tobytes()

    tex = Texture()
    tex.setup_2d_texture(width, height, Texture.T_unsigned_byte, Texture.F_rgba)  # type: ignore
    tex.set_ram_image(raw_data)  # type: ignore

    tex.set_minfilter(SamplerState.FT_linear)  # type: ignore
    tex.set_magfilter(SamplerState.FT_linear)  # type: ignore
    tex.set_wrap_u(SamplerState.WM_clamp)  # type: ignore
    tex.set_wrap_v(SamplerState.WM_clamp)  # type: ignore

    return tex


def normalize_to_byte(value: float) -> int:
    """Convert a normalized float (0.0–1.0) to a byte value (0–255)."""
    return max(0, min(255, int(round(value * 255))))


def normalize_color_to_bytes(color: tuple[float, ...]) -> tuple[int, ...]:
    """Convert a tuple of normalized floats to a tuple of byte values."""
    return tuple(normalize_to_byte(c) for c in color)


def _copy_texture(src: KivyTexture) -> KivyTexture:
    try:
        pixels = src.pixels  # type: ignore
        new_tex: KivyTexture = KivyTexture.create(size=src.size, colorfmt=src.colorfmt)
        new_tex.blit_buffer(pixels, colorfmt=src.colorfmt, bufferfmt="ubyte")
        try:
            new_tex.min_filter = src.min_filter
            new_tex.mag_filter = src.mag_filter
            new_tex.wrap = src.wrap
        except Exception:
            pass
        return new_tex
    except Exception:
        # Some backends (e.g., certain GLES paths) can’t read pixels; return shared texture.
        return src


def clone_image_widget(
    img: KivyImage,
    *,
    deep_texture: bool = False,
    copy_layout_props: Iterable[str] = (
        "size_hint",
        "size",
        "pos_hint",
        "opacity",
        "color",
        "allow_stretch",
        "keep_ratio",
        "mipmap",
        "anim_delay",
    ),
) -> KivyImage:
    clone = KivyImage()

    for name in copy_layout_props:
        if hasattr(img, name):
            try:
                setattr(clone, name, getattr(img, name))
            except Exception:
                pass

    if img.source:
        if deep_texture:
            clone.nocache = True
        clone.source = img.source
    elif img.texture is not None:
        clone.texture = _copy_texture(img.texture) if deep_texture else img.texture

    return clone
