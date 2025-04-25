from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


def draw_text_on_image(
    base_image: Image.Image,
    text_entries: list[tuple[str, tuple[int, int]]],
    font_path: str,
    font_size: int = 16,
    text_color: Tuple[float, float, float, float] = (255, 255, 255, 255),
) -> Image.Image:
    """
    Draw multiple pieces of text on an image at given positions.

    :param base_image: PIL Image object to draw on.
    :param text_entries: List of tuples (text, (x, y)) where text is the string and (x, y) is position.
    :param font_path: Optional path to a .ttf font file. Uses default font if None.
    :param font_size: Size of the font.
    :return: Modified PIL Image with text drawn.
    """
    draw = ImageDraw.Draw(base_image)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

    for text, position in text_entries:
        draw.text(position, text, font=font, fill=tuple(map(int, text_color)))

    return base_image


def create_stacked_horizontal_images(images: list[Image.Image], offset: Tuple[int, int] = (10, 0)) -> Image.Image:
    """
    Stack images horizontally with each new image offset down and to the right, like a fan layout.

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

    composite = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    for i, img in enumerate(images):
        composite.paste(img, (i * x_off, i * y_off), img)

    return composite
