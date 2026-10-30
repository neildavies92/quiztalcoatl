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

BACKGROUND = "#071F26"
INK = "#062329"
TEAL = "#17634F"
SURFACE = "#12383E"
MUTED = "#BDD7CD"
GOLD = "#FFD45B"
CORAL = "#FF976A"
WHITE = "#F7FFF7"
LINE = "#2E6763"


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
    brand_box: Box | None = None
    brand_source: Path | None = None
    design_status: str = "Visual proposal; human design UAT pending"


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
    color: str = WHITE,
    background: str = BACKGROUND,
    max_lines: int = 1,
    align: Literal["left", "center"] = "left",
    balance: bool = False,
) -> None:
    if not text.strip():
        raise GraphicsError(f"{role}: text must not be empty")
    lower = minimum if minimum is not None else size
    for candidate in range(size, lower - 1, -1):
        font = fonts.at(candidate, bold=bold)
        lines = _lines(text, font, box.width)
        if balance and lines is not None and len(lines) == 2 and "\n" not in text:
            words = text.split()
            pairs = [
                (" ".join(words[:split]), " ".join(words[split:])) for split in range(1, len(words))
            ]
            fitting = [
                pair for pair in pairs if all(font.getlength(line) <= box.width for line in pair)
            ]
            if fitting:
                lines = min(
                    fitting, key=lambda pair: abs(font.getlength(pair[0]) - font.getlength(pair[1]))
                )
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


def _brand(path: Path) -> Image.Image:
    try:
        if not path.is_file():
            raise GraphicsError(f"brand asset must be a regular PNG file: {path}")
        with Image.open(path) as image:
            if image.format != "PNG":
                raise GraphicsError(f"brand asset must contain PNG data: {path}")
            image.verify()
        with Image.open(path) as image:
            artwork = image.convert("RGBA")
            alpha = artwork.getchannel("A")
            if alpha.getextrema()[0] != 0 or alpha.getbbox() is None:
                raise GraphicsError(
                    "brand asset must contain visible artwork on a truly transparent PNG "
                    f"background: {path}"
                )
            return artwork
    except (OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise GraphicsError(f"Cannot read brand asset {path}: {exc}") from exc


def _fitted_box(source_size: tuple[int, int], maximum: Box) -> Box:
    scale = min(maximum.width / source_size[0], maximum.height / source_size[1])
    size = tuple(max(1, round(value * scale)) for value in source_size)
    return Box(
        maximum.x + (maximum.width - size[0]) // 2,
        maximum.y + (maximum.height - size[1]) // 2,
        size[0],
        size[1],
    )


def render_card(
    question: ResolvedQuestion,
    layout: CardLayout,
    *,
    content_root: Path,
    fonts: FontSet,
    reveal: bool = False,
    brand_asset: Path | None = None,
) -> RenderedCard:
    """Render an energetic static flag question/reveal without selecting editorial content.

    The caller supplies genuinely approved content or explicitly synthetic fixtures.
    Optional brand artwork is an explicit local PNG, never an inferred or fetched logo.
    """
    question = ResolvedQuestion.model_validate_json(question.model_dump_json())
    if question.ordinal > layout.total_questions:
        raise GraphicsError("question ordinal exceeds total_questions")
    flag, source = _flag(question, content_root)
    image = Image.new("RGB", (1920, 1080), BACKGROUND)
    draw = ImageDraw.Draw(image)
    blocks: list[TextBlock] = []
    # Restrained stadium-like depth, with no decoration behind critical text.
    draw.polygon([(0, 270), (960, 120), (1920, 270), (1920, 748), (0, 748)], fill="#0A2C32")
    draw.polygon([(0, 460), (600, 300), (1200, 748), (0, 748)], fill="#0C363A")
    draw.polygon([(1590, 0), (1920, 0), (1920, 500)], fill="#0D383A")
    # Keep the complete text header on one actual, audited dark surface.
    draw.rectangle((0, 0, 1920, 320 if reveal else 280), fill=BACKGROUND)
    draw.line([(72, 138), (1848, 138)], fill=LINE, width=2)
    draw.rounded_rectangle((72, 136, 340, 141), radius=2, fill=GOLD)
    draw.line([(1774, 142), (1848, 142)], fill=CORAL, width=5)
    _text(
        draw,
        blocks,
        fonts,
        "brand",
        "QUIZtalcoatl",
        Box(72, 72, 460, 50),
        size=35,
        bold=True,
        color=GOLD,
    )
    pip_width = max(3, min(26, (558 - 6 * (layout.total_questions - 1)) // layout.total_questions))
    gap = 6
    total_width = layout.total_questions * pip_width + (layout.total_questions - 1) * gap
    start = 960 - total_width // 2
    for index in range(layout.total_questions):
        color = (
            GOLD
            if index == question.ordinal - 1
            else (TEAL if index < question.ordinal - 1 else SURFACE)
        )
        x = start + index * (pip_width + gap)
        draw.rounded_rectangle((x, 88, x + pip_width, 104), radius=6, fill=color)
    _text(
        draw,
        blocks,
        fonts,
        "progress",
        f"{question.ordinal:02} / {layout.total_questions:02}",
        Box(1580, 72, 268, 50),
        size=34,
        bold=True,
        align="center",
        color=WHITE,
    )
    if reveal:
        draw.rounded_rectangle((704, 156, 1216, 202), radius=22, fill=GOLD)
        _text(
            draw,
            blocks,
            fonts,
            "eyebrow",
            "CORRECT ANSWER",
            Box(718, 163, 484, 32),
            size=24,
            bold=True,
            align="center",
            color=INK,
            background=GOLD,
        )
        headline, headline_box = question.correct_answer.label, Box(72, 216, 1776, 100)
        headline_color = GOLD
    else:
        headline, headline_box = question.prompt, Box(72, 162, 1776, 118)
        headline_color = WHITE
    _text(
        draw,
        blocks,
        fonts,
        "headline",
        headline,
        headline_box,
        size=78,
        minimum=52,
        max_lines=1 if reveal else 2,
        bold=True,
        align="center",
        color=headline_color,
    )
    maximum = Box(144, 328 if reveal else 294, 1100, 278 if reveal else 440)
    flag_box = _fitted_box(flag.size, maximum)
    # The flag floats directly in the hero area, with its own subtle edge and shadow.
    draw.rectangle(
        (
            flag_box.x + 11,
            flag_box.y + 14,
            flag_box.x + flag_box.width + 11,
            flag_box.y + flag_box.height + 14,
        ),
        fill="#03181C",
    )
    draw.rectangle(flag_box.bounds, fill=WHITE)
    resized = flag.resize((flag_box.width, flag_box.height), Image.Resampling.LANCZOS)
    image.paste(resized, (flag_box.x, flag_box.y), resized)
    draw.rectangle(flag_box.bounds, outline="#577977", width=2)
    brand_box: Box | None = None
    brand_source: Path | None = None
    if brand_asset is not None:
        artwork = _brand(brand_asset)
        brand_source = brand_asset.resolve()
        brand_box = _fitted_box(
            artwork.size, Box(1270, 294 if reveal else 264, 560, 320 if reveal else 470)
        )
        artwork = artwork.resize((brand_box.width, brand_box.height), Image.Resampling.LANCZOS)
        image.paste(artwork, (brand_box.x, brand_box.y), artwork)
    if reveal:
        draw.rounded_rectangle((72, 626, 1848, 744), radius=18, fill=SURFACE)
        draw.rounded_rectangle((72, 626, 82, 744), radius=5, fill=CORAL)
        _text(
            draw,
            blocks,
            fonts,
            "fact-label",
            "FLAG\nFACT",
            Box(104, 652, 124, 64),
            size=23,
            max_lines=2,
            bold=True,
            color=GOLD,
            background=SURFACE,
        )
        _text(
            draw,
            blocks,
            fonts,
            "explanation",
            question.explanation.text,
            Box(260, 636, 1556, 96),
            size=38,
            minimum=34,
            max_lines=2,
            color=WHITE,
            background=SURFACE,
            balance=True,
        )
    for index, option in enumerate(question.options):
        selected = reveal and index == question.correct_answer_index
        box = Box(72 + (index % 2) * 910, 764 + (index // 2) * 132, 866, 112)
        fill, color = (GOLD, INK) if selected else (SURFACE, WHITE)
        draw.rounded_rectangle(
            (box.x, box.y + 7, box.x + box.width, box.y + box.height + 7), radius=22, fill="#03181C"
        )
        draw.rounded_rectangle(
            box.bounds,
            radius=22,
            fill=fill,
            outline=GOLD if selected else LINE,
            width=4 if selected else 2,
        )
        draw.rounded_rectangle(
            (box.x + 8, box.y + 8, box.x + 108, box.y + 104),
            radius=16,
            fill=INK if selected else TEAL,
        )
        _text(
            draw,
            blocks,
            fonts,
            f"option-letter-{index}",
            chr(65 + index),
            Box(box.x + 17, box.y + 20, 82, 76),
            size=53,
            bold=True,
            align="center",
            color=GOLD,
            background=INK if selected else TEAL,
        )
        _text(
            draw,
            blocks,
            fonts,
            f"option-{index}",
            option.label,
            Box(box.x + 138, box.y + 10, 700, 94),
            size=48,
            minimum=36,
            max_lines=2,
            bold=True,
            color=color,
            background=fill,
        )
    if layout.preview_label:
        _text(
            draw,
            blocks,
            fonts,
            "preview-label",
            layout.preview_label,
            Box(72, 1030, 1776, 28),
            size=18,
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
        brand_box,
        brand_source,
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
    for source in (card.source_asset, card.brand_source):
        if source is not None and (
            destination == source or (destination.exists() and destination.samefile(source))
        ):
            raise GraphicsError("output must not replace a source flag asset or brand asset")
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
