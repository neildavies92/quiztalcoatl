"""Static geography-pilot cards; resolved editorial content is never selected here."""

import io
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from quiztalcoatl.content import ContentError, check_asset
from quiztalcoatl.models import ResolvedQuestion

PAPER = "#F4F1E8"
INK = "#183B3D"
TEAL = "#145C56"
MUTED = "#506665"
GOLD = "#F1C86C"
WHITE = "#FFFFFF"
LINE = "#D9E1D8"


class GraphicsError(ValueError):
    """A graphics prerequisite, layout or local output cannot be satisfied."""


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.width, self.y + self.height

    def contains(self, other: "Box") -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.x + self.width >= other.x + other.width
            and self.y + self.height >= other.y + other.height
        )


@dataclass(frozen=True)
class CardLayout:
    """Explicit sequence context; geography-pilot geometry remains one fixed layout."""

    total_questions: int
    preview_label: str | None = None

    def __post_init__(self) -> None:
        if type(self.total_questions) is not int or not 1 <= self.total_questions <= 99:
            raise GraphicsError("total_questions must be an integer from 1 to 99")
        if self.preview_label is not None and not self.preview_label.strip():
            raise GraphicsError("preview_label must contain visible text")


@dataclass(frozen=True)
class FontSet:
    """Explicit FreeType faces, injectable for controlled tests."""

    regular: ImageFont.FreeTypeFont
    bold: ImageFont.FreeTypeFont

    def at(self, size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
        return (self.bold if bold else self.regular).font_variant(size=size)


def load_fonts(font_dir: Path | None = None) -> FontSet:
    """Load documented DejaVu files, never search implicit workstation font paths."""
    configured = font_dir if font_dir is not None else os.environ.get("QUIZTALCOATL_FONT_DIR")
    if not configured:
        raise GraphicsError(
            "Fonts unavailable: supply font_dir or QUIZTALCOATL_FONT_DIR containing "
            "DejaVuSans.ttf and DejaVuSans-Bold.ttf. The Docker runtime provides these."
        )
    root = Path(configured)
    try:
        return FontSet(
            ImageFont.truetype(io.BytesIO((root / "DejaVuSans.ttf").read_bytes()), size=40),
            ImageFont.truetype(io.BytesIO((root / "DejaVuSans-Bold.ttf").read_bytes()), size=40),
        )
    except OSError as exc:
        raise GraphicsError(
            f"Cannot load required DejaVu regular/Bold fonts from {root}: {exc}"
        ) from exc


@dataclass(frozen=True)
class TextBlock:
    role: str
    text: str
    lines: tuple[str, ...]
    size: int
    box: Box
    ink_boxes: tuple[Box, ...]
    foreground: str
    background: str


@dataclass
class RenderedCard:
    """Image plus measured geometry for diagnostics and reproducible layout tests."""

    image: Image.Image
    text_blocks: tuple[TextBlock, ...]
    flag_box: Box
    flag_source_size: tuple[int, int]
    option_ids: tuple[str, ...]
    highlighted_index: int | None
    source_asset: Path


def contrast_ratio(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return sum(
            channel * weight
            for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
        )

    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _lines(text: str, font: ImageFont.FreeTypeFont, width: int) -> tuple[str, ...] | None:
    result: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            result.append("")
            continue
        current = ""
        for word in words:
            if font.getlength(word) > width:
                return None
            trial = f"{current} {word}" if current else word
            if font.getlength(trial) > width:
                result.append(current)
                current = word
            else:
                current = trial
        result.append(current)
    return tuple(result)


def _text(
    draw: ImageDraw.ImageDraw,
    blocks: list[TextBlock],
    fonts: FontSet,
    role: str,
    text: str,
    box: Box,
    *,
    size: int,
    minimum: int | None = None,
    bold: bool = False,
    color: str = INK,
    background: str = PAPER,
    max_lines: int = 1,
    align: Literal["left", "center"] = "left",
) -> None:
    if not text.strip():
        raise GraphicsError(f"{role}: text must not be empty")
    lower = minimum if minimum is not None else size
    for candidate in range(size, lower - 1, -1):
        font = fonts.at(candidate, bold=bold)
        lines = _lines(text, font, box.width)
        advance = math.ceil(candidate * 1.22)
        if lines is None or len(lines) > max_lines or advance * len(lines) > box.height:
            continue
        top = box.y + (box.height - advance * len(lines)) // 2
        measured: list[Box] = []
        for index, line in enumerate(lines):
            left, upper, right, bottom = draw.textbbox((0, 0), line, font=font, anchor="lt")
            width, height = math.ceil(right - left), math.ceil(bottom - upper)
            x = box.x + ((box.width - width) // 2 if align == "center" else 0)
            y = top + index * advance
            ink = Box(x, y, width, height)
            if not box.contains(ink):
                break
            measured.append(ink)
        else:
            for line, ink in zip(lines, measured, strict=True):
                left, upper, _, _ = draw.textbbox((0, 0), line, font=font, anchor="lt")
                draw.text((ink.x - left, ink.y - upper), line, font=font, fill=color, anchor="lt")
            blocks.append(
                TextBlock(role, text, lines, candidate, box, tuple(measured), color, background)
            )
            return
    raise GraphicsError(
        f"{role}: text cannot fit {box.width}×{box.height} at minimum {lower}px / "
        f"{max_lines} lines; shorten the reviewed text or revise the layout explicitly"
    )


def _flag(question: ResolvedQuestion, root: Path) -> tuple[Image.Image, Path]:
    try:
        check_asset(question.asset, root, required=True, png=True)
        path = (root.resolve() / question.asset.path).resolve()
        with Image.open(path) as image:
            return image.convert("RGBA"), path
    except (ContentError, OSError) as exc:
        raise GraphicsError(f"flag for {question.question_id}: {exc}") from exc


def render_card(
    question: ResolvedQuestion,
    layout: CardLayout,
    *,
    content_root: Path,
    fonts: FontSet,
    reveal: bool = False,
) -> RenderedCard:
    """Render one static question or reveal, preserving resolved answers and asset ratio.

    The caller must supply a genuinely approved manifest or clearly labelled synthetic
    test content. Graphics do not confer editorial approval or resolve questions.
    """
    # Revalidate mutable models so invalid answer indices cannot silently change the display.
    question = ResolvedQuestion.model_validate_json(question.model_dump_json())
    if question.ordinal > layout.total_questions:
        raise GraphicsError("question ordinal exceeds total_questions")
    flag, source = _flag(question, content_root)
    image = Image.new("RGB", (1920, 1080), PAPER)
    draw = ImageDraw.Draw(image)
    blocks: list[TextBlock] = []
    # A restrained edge accent and atlas-like coordinate lines establish a repeatable frame.
    draw.rectangle((0, 0, 1920, 12), fill=TEAL)
    draw.line((72, 166, 1848, 166), fill=LINE, width=2)
    draw.rounded_rectangle((72, 72, 136, 136), radius=14, outline=MUTED, width=2)
    _text(
        draw,
        blocks,
        fonts,
        "mascot-placeholder",
        "ART\nTBC",
        Box(77, 78, 54, 48),
        size=13,
        max_lines=2,
        align="center",
        color=MUTED,
    )
    _text(draw, blocks, fonts, "brand", "QUIZtalcoatl", Box(156, 72, 500, 56), size=43, bold=True)
    _text(
        draw,
        blocks,
        fonts,
        "brand-status",
        "PROPOSED WORDMARK • MASCOT PENDING",
        Box(158, 128, 660, 24),
        size=16,
        color=MUTED,
    )
    _text(
        draw,
        blocks,
        fonts,
        "series",
        "GEOGRAPHY / FLAGS",
        Box(940, 82, 490, 38),
        size=25,
        bold=True,
        color=TEAL,
    )
    draw.rounded_rectangle((1500, 72, 1848, 140), radius=34, fill=INK)
    _text(
        draw,
        blocks,
        fonts,
        "progress",
        f"QUESTION {question.ordinal:02} / {layout.total_questions:02}",
        Box(1515, 85, 318, 38),
        size=25,
        bold=True,
        color=WHITE,
        background=INK,
        align="center",
    )
    eyebrow = "THE ANSWER IS" if reveal else "NAME THE COUNTRY"
    _text(
        draw,
        blocks,
        fonts,
        "eyebrow",
        eyebrow,
        Box(72, 190, 1056, 34),
        size=23,
        color=TEAL,
        bold=True,
    )
    headline = question.correct_answer.label if reveal else question.prompt
    _text(
        draw,
        blocks,
        fonts,
        "headline",
        headline,
        Box(72, 236, 1056, 146),
        size=62,
        minimum=48,
        max_lines=2,
        bold=True,
    )
    _text(
        draw,
        blocks,
        fonts,
        "options-heading",
        "CORRECT ANSWER" if reveal else "CHOOSE YOUR ANSWER",
        Box(1200, 190, 648, 34),
        size=23,
        bold=True,
        color=TEAL,
    )
    panel = Box(72, 386, 1056, 414)
    draw.rounded_rectangle(
        (panel.x, panel.y + 8, panel.x + panel.width, panel.y + panel.height + 8),
        radius=28,
        fill="#E4E5DC",
    )
    draw.rounded_rectangle(panel.bounds, radius=28, fill=WHITE, outline=LINE, width=2)
    maximum = Box(128, 421, 944, 344)
    scale = min(maximum.width / flag.width, maximum.height / flag.height)
    flag_size = (max(1, round(flag.width * scale)), max(1, round(flag.height * scale)))
    flag_box = Box(
        maximum.x + (maximum.width - flag_size[0]) // 2,
        maximum.y + (maximum.height - flag_size[1]) // 2,
        *flag_size,
    )
    resized = flag.resize(flag_size, Image.Resampling.LANCZOS)
    image.paste(resized, (flag_box.x, flag_box.y), resized)
    draw.rectangle(flag_box.bounds, outline=LINE, width=1)
    for index, option in enumerate(question.options):
        selected = reveal and index == question.correct_answer_index
        box = Box(1200, 244 + index * 146, 648, 126)
        fill, color = (TEAL, WHITE) if selected else (WHITE, INK)
        draw.rounded_rectangle(
            (box.x, box.y + 5, box.x + box.width, box.y + box.height + 5), radius=24, fill="#E4E5DC"
        )
        draw.rounded_rectangle(
            box.bounds,
            radius=24,
            fill=fill,
            outline=TEAL if selected else LINE,
            width=3 if selected else 2,
        )
        badge = Box(box.x + 22, box.y + 35, 56, 56)
        draw.ellipse(badge.bounds, fill=GOLD if selected else PAPER)
        _text(
            draw,
            blocks,
            fonts,
            f"option-letter-{index}",
            chr(65 + index),
            Box(badge.x, badge.y + 1, 56, 48),
            size=29,
            bold=True,
            align="center",
            color=INK,
            background=GOLD if selected else PAPER,
        )
        _text(
            draw,
            blocks,
            fonts,
            f"option-{index}",
            option.label,
            Box(box.x + 102, box.y + 14, 520, 98),
            size=43,
            minimum=36,
            max_lines=2,
            bold=True,
            color=color,
            background=fill,
        )
    footer = Box(72, 846, 1776, 162)
    draw.rounded_rectangle(footer.bounds, radius=24, fill=INK if reveal else "#E5EBE2")
    _text(
        draw,
        blocks,
        fonts,
        "footer-label",
        "DID YOU KNOW?" if reveal else "YOUR NEXT MOVE",
        Box(104, 860, 1712, 34),
        size=22,
        color=GOLD if reveal else TEAL,
        background=INK if reveal else "#E5EBE2",
        bold=True,
    )
    _text(
        draw,
        blocks,
        fonts,
        "explanation" if reveal else "instruction",
        question.explanation.text
        if reveal
        else "Pick A, B, C or D. What does your geography instinct say?",
        Box(104, 903, 1712, 86),
        size=38,
        minimum=34,
        max_lines=2,
        color=WHITE if reveal else INK,
        background=INK if reveal else "#E5EBE2",
    )
    if layout.preview_label:
        _text(
            draw,
            blocks,
            fonts,
            "preview-label",
            layout.preview_label,
            Box(72, 1024, 1776, 28),
            size=19,
            color=MUTED,
            align="center",
        )
    return RenderedCard(
        image,
        tuple(blocks),
        flag_box,
        flag.size,
        tuple(option.country_id for option in question.options),
        question.correct_answer_index if reveal else None,
        source,
    )


def save_png(card: RenderedCard, output_root: Path, path: str, *, overwrite: bool = False) -> Path:
    """Write a complete PNG under an explicit output root, preserving its input asset."""
    relative = PurePosixPath(path)
    if (
        not path
        or relative.is_absolute()
        or PureWindowsPath(path).drive
        or ".." in relative.parts
        or "\\" in path
        or "\x00" in path
        or relative.suffix.lower() != ".png"
    ):
        raise GraphicsError("output path must be a relative .png path without traversal")
    root = output_root.resolve()
    requested = root / path
    if requested.is_symlink():
        raise GraphicsError("output path must not be a symlink")
    destination = requested.resolve()
    if not destination.is_relative_to(root):
        raise GraphicsError("output path escapes output root through a symlink")
    if destination == card.source_asset or (
        destination.exists() and destination.samefile(card.source_asset)
    ):
        raise GraphicsError("output must not replace the source flag asset")
    if destination.exists() and not overwrite:
        raise GraphicsError("output already exists; explicitly request overwrite")
    temporary: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=".png", delete=False
        ) as stream:
            temporary = Path(stream.name)
            card.image.save(stream, format="PNG", optimize=False)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)
    except OSError as exc:
        raise GraphicsError(f"Cannot save PNG {destination}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
