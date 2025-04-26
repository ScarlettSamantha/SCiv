from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont


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

    composite = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    # Reverse images: first ones behind
    for i, img in enumerate(images):
        # Compute position relative to reverse stacking
        pos = (i * x_off, i * y_off)
        composite.alpha_composite(img, dest=pos)

    return composite
