"""Distinctive static publication artwork built on the existing Pillow brand tools."""

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from quiztalcoatl.graphics import (
    BACKGROUND,
    CORAL,
    GOLD,
    INK,
    LINE,
    TEAL,
    WHITE,
    Box,
    FontSet,
    GraphicsError,
    TextBlock,
    _brand,
    _fitted_box,
    _flag,
    _text,
)
from quiztalcoatl.models import ResolvedQuestion


@dataclass
class RenderedThumbnail:
    image: Image.Image
    text_blocks: tuple[TextBlock, ...]
    flag_boxes: tuple[Box, ...]
    flag_source_sizes: tuple[tuple[int, int], ...]
    brand_box: Box
    brand_source_size: tuple[int, int]


def render_thumbnail(
    questions: list[ResolvedQuestion],
    *,
    hook: str,
    question_count: int,
    content_root: Path,
    fonts: FontSet,
    brand_asset: Path,
) -> RenderedThumbnail:
    """Compose validated question artwork; publication.generate_package owns approval checks.

    This low-level drawing function also supports explicitly synthetic review fixtures.
    It does not assert editorial approval or select countries.
    """
    if len(questions) < 3 or question_count != len(questions):
        raise GraphicsError("thumbnail requires at least three ordered questions and exact count")
    if (
        not hook.strip()
        or len(hook) > 120
        or any(ord(character) < 32 and character != "\n" for character in hook)
    ):
        raise GraphicsError("thumbnail hook must contain 1–120 characters; shorten reviewed copy")
    artwork = _brand(brand_asset)
    image = Image.new("RGB", (1280, 720), BACKGROUND)
    draw = ImageDraw.Draw(image)
    # Poster-like diagonal stage, rather than a miniature multiple-choice question card.
    draw.polygon([(756, 0), (1280, 0), (1280, 720), (1000, 720), (654, 250)], fill=TEAL)
    draw.polygon([(1240, 0), (1280, 0), (1280, 720), (1206, 720), (1020, 250)], fill="#227B60")
    draw.ellipse((740, 152, 1244, 656), fill="#0C363A", outline=LINE, width=3)
    draw.line([(48, 133), (664, 133)], fill=GOLD, width=5)
    draw.line([(670, 133), (720, 133)], fill=CORAL, width=5)
    blocks: list[TextBlock] = []
    _text(
        draw,
        blocks,
        fonts,
        "brand",
        "QUIZtalcoatl",
        Box(48, 47, 650, 64),
        size=46,
        bold=True,
        color=GOLD,
    )
    _text(
        draw,
        blocks,
        fonts,
        "hook",
        hook,
        Box(48, 164, 688, 263),
        size=85,
        minimum=64,
        max_lines=3,
        bold=True,
        color=WHITE,
        balance=True,
    )
    brand_box = _fitted_box(artwork.size, Box(760, 147, 460, 476))
    resized = artwork.resize((brand_box.width, brand_box.height), Image.Resampling.LANCZOS)
    image.paste(resized, (brand_box.x, brand_box.y), resized)
    boxes: list[Box] = []
    sizes: list[tuple[int, int]] = []
    for index, question in enumerate(questions[:3]):
        flag, _ = _flag(question, content_root)
        maximum = Box(58 + index * 224, 464, 192, 128)
        box = _fitted_box(flag.size, maximum)
        draw.rounded_rectangle(
            (maximum.x - 10, 450, maximum.x + 202, 606),
            radius=14,
            fill="#03181C",
            outline=LINE,
            width=2,
        )
        fitted = flag.resize((box.width, box.height), Image.Resampling.LANCZOS)
        image.paste(fitted, (box.x, box.y), fitted)
        draw.rectangle(box.bounds, outline=WHITE, width=2)
        boxes.append(box)
        sizes.append(flag.size)
    draw.rounded_rectangle((48, 633, 714, 686), radius=22, fill=GOLD)
    _text(
        draw,
        blocks,
        fonts,
        "challenge",
        f"{question_count} FLAGS  •  HOW MANY CAN YOU NAME?",
        Box(66, 641, 630, 37),
        size=26,
        bold=True,
        color=INK,
        background=GOLD,
        align="center",
    )
    return RenderedThumbnail(
        image, tuple(blocks), tuple(boxes), tuple(sizes), brand_box, artwork.size
    )


def encode_thumbnail(thumbnail: RenderedThumbnail) -> bytes:
    """Export an upload-portable RGB PNG under the stricter mobile file limit."""
    if thumbnail.image.size != (1280, 720) or thumbnail.image.mode != "RGB":
        raise GraphicsError("thumbnail must be RGB 1280×720")
    buffer = io.BytesIO()
    thumbnail.image.save(buffer, format="PNG", optimize=False)
    payload = buffer.getvalue()
    if len(payload) >= 2_000_000:
        raise GraphicsError("thumbnail PNG exceeds the conservative 2 MB upload limit")
    return payload
