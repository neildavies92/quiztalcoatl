"""Controlled-font graphics tests using explicitly synthetic approved resolver inputs."""

import hashlib
import io
import socket
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw, ImageFont
from test_resolver import SyntheticInputs
from test_resolver import inputs as inputs

from quiztalcoatl.graphics import (
    BACKGROUND,
    GOLD,
    INK,
    SURFACE,
    TEAL,
    WHITE,
    Box,
    CardLayout,
    FontSet,
    GraphicsError,
    contrast_ratio,
    load_fonts,
    render_card,
    save_png,
)
from quiztalcoatl.models import ResolvedQuestion
from quiztalcoatl.resolver import resolve_files


@pytest.fixture
def fonts() -> FontSet:
    # Pillow embeds Aileron bytes: controlled, test-only, with no workstation font lookup.
    regular = ImageFont.load_default(size=40)
    assert isinstance(regular, ImageFont.FreeTypeFont)
    return FontSet(regular, regular.font_variant(size=40))


@pytest.fixture
def question(inputs: SyntheticInputs) -> ResolvedQuestion:
    return resolve_files(inputs.countries_path, inputs.recipe_path).questions[0]


def test_question_png_size_determinism_and_original_content(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    layout = CardLayout(total_questions=15)
    first = render_card(question, layout, content_root=inputs.root, fonts=fonts)
    second = render_card(question, layout, content_root=inputs.root, fonts=fonts)
    assert first.image.size == (1920, 1080)
    assert first.image.tobytes() == second.image.tobytes()
    output = save_png(first, inputs.root / "output", "question.png")
    with Image.open(output) as image:
        assert image.format == "PNG" and image.size == (1920, 1080)
    assert first.option_ids == tuple(option.country_id for option in question.options)
    assert first.highlighted_index is None
    assert (
        next(block.text for block in first.text_blocks if block.role == "headline")
        == question.prompt
    )
    assert next(block.text for block in first.text_blocks if block.role == "progress") == "01 / 15"


def test_recorded_geometry_matches_actual_text_draws_and_option_order(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    original = ImageDraw.ImageDraw.text
    drawn: list[str] = []

    def record(self: ImageDraw.ImageDraw, xy: Any, text: str, *args: Any, **kwargs: Any) -> None:
        drawn.append(text)
        original(self, xy, text, *args, **kwargs)

    with patch("PIL.ImageDraw.ImageDraw.text", autospec=True, side_effect=record):
        card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    assert drawn == [line for block in card.text_blocks for line in block.lines]
    labels = [
        block.text
        for block in card.text_blocks
        if block.role in {"option-0", "option-1", "option-2", "option-3"}
    ]
    assert labels == [option.label for option in question.options]
    assert question.prompt in drawn


def test_reveal_uses_resolved_correct_answer_and_fact(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts, reveal=True)
    assert card.highlighted_index == question.correct_answer_index
    blocks = {block.role: block for block in card.text_blocks}
    assert blocks["headline"].text == question.correct_answer.label
    assert blocks["explanation"].text == question.explanation.text
    assert blocks[f"option-{question.correct_answer_index}"].foreground == INK
    assert blocks[f"option-{question.correct_answer_index}"].background == GOLD
    # Verify the selected card's actual fill, rather than trusting only diagnostics.
    index = question.correct_answer_index
    x = 72 + (index % 2) * 910
    y = 764 + (index // 2) * 132
    assert card.image.getpixel((x + 836, y + 56)) == (255, 212, 91)


@pytest.mark.parametrize(
    "dimensions", [(1200, 800), (1200, 600), (900, 900), (500, 800), (1900, 400)]
)
def test_flag_aspect_ratio_and_bounds(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, dimensions: tuple[int, int]
) -> None:
    path = inputs.root / "ratio.png"
    Image.new("RGB", dimensions, "red").save(path)
    question.asset.path = path.name
    question.asset.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    box = card.flag_box
    assert Box(144, 294, 1100, 440).contains(box)
    scale = min(1100 / dimensions[0], 440 / dimensions[1])
    assert (box.width, box.height) == tuple(max(1, round(value * scale)) for value in dimensions)
    assert card.flag_source_size == dimensions
    assert card.image.getpixel((box.x + box.width // 2, box.y + box.height // 2)) == (255, 0, 0)


@pytest.mark.parametrize("reveal", [False, True])
def test_text_measured_inside_safe_margins_and_contrast(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, reveal: bool
) -> None:
    card = render_card(
        question, CardLayout(15), content_root=inputs.root, fonts=fonts, reveal=reveal
    )
    safe = Box(72, 72, 1776, 936)
    for block in card.text_blocks:
        for ink in block.ink_boxes:
            assert block.box.contains(ink), block.role
            assert safe.contains(ink), block.role
        assert contrast_ratio(block.foreground, block.background) >= 4.5, block.role
    for block in card.text_blocks:
        if block.role.startswith("option-") and "letter" not in block.role:
            assert block.size >= 36


def test_long_labels_and_explanation_wrap_without_clipping(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    for option in question.options:
        option.label = f"Federated Northern Archipelago {option.country_id[-2:]}"
    question.correct_answer = question.options[question.correct_answer_index].model_copy(deep=True)
    question.explanation.text = (
        "This synthetic archipelago uses a gold triangle for curiosity "
        "and an ivory band for shared "
        "knowledge, while its coral sun represents discovery across the many fictional islands."
    )
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts, reveal=True)
    for block in card.text_blocks:
        assert len(block.lines) <= 2
        assert all(block.box.contains(ink) for ink in block.ink_boxes)
    assert len(next(block.lines for block in card.text_blocks if block.role == "explanation")) == 2


@pytest.mark.parametrize("field", ["answer", "explanation", "prompt"])
def test_impossible_text_is_rejected_explicitly(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, field: str
) -> None:
    if field == "answer":
        question.options[0].label = "Unbreakable" * 40
        if question.correct_answer_index == 0:
            question.correct_answer = question.options[0].model_copy(deep=True)
    elif field == "explanation":
        question.explanation.text = "Long explanation " * 29
    else:
        question.prompt = "Unbreakable" * 40
    with pytest.raises(GraphicsError, match="cannot fit.*minimum"):
        render_card(
            question,
            CardLayout(15),
            content_root=inputs.root,
            fonts=fonts,
            reveal=field == "explanation",
        )


def test_missing_fonts_are_actionable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("QUIZTALCOATL_FONT_DIR", raising=False)
    with pytest.raises(GraphicsError, match="QUIZTALCOATL_FONT_DIR"):
        load_fonts()
    with pytest.raises(GraphicsError, match="DejaVu regular/Bold"):
        load_fonts(tmp_path)


def test_explicit_font_directory_and_environment(
    tmp_path: Path, fonts: FontSet, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Test-only temporary copies of Pillow's embedded Aileron face exercise file loading.
    # Their filenames simulate the interface; these are not DejaVu production previews.
    embedded = fonts.regular.path
    assert isinstance(embedded, io.BytesIO)
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        (tmp_path / name).write_bytes(embedded.getvalue())
    loaded = load_fonts(tmp_path)
    assert loaded.regular.getname() == fonts.regular.getname()
    assert isinstance(loaded.regular.path, io.BytesIO)
    assert isinstance(loaded.bold.path, io.BytesIO)
    monkeypatch.setenv("QUIZTALCOATL_FONT_DIR", str(tmp_path))
    assert load_fonts().bold.getname() == fonts.regular.getname()
    (tmp_path / "DejaVuSans-Bold.ttf").write_bytes(b"corrupt font")
    with pytest.raises(GraphicsError, match="Cannot load"):
        load_fonts(tmp_path)


@pytest.mark.parametrize("failure", ["missing", "corrupt", "checksum", "escape"])
def test_bad_flag_is_actionable(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, failure: str
) -> None:
    path = inputs.root / "test-only.png"
    if failure == "missing":
        path.unlink()
    elif failure == "corrupt":
        path.write_bytes(b"not PNG")
        question.asset.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    elif failure == "checksum":
        question.asset.sha256 = "0" * 64
    else:
        link = inputs.root / "escape.png"
        link.symlink_to(inputs.root.parent / "outside.png")
        question.asset.path = link.name
    with pytest.raises(GraphicsError, match="flag for v-001"):
        render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)


def test_no_input_mutation_or_network(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    before = question.model_dump_json()
    bytes_before = (inputs.root / "test-only.png").read_bytes()
    with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
        card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
        save_png(card, inputs.root / "output", "offline.png")
    assert before == question.model_dump_json()
    assert bytes_before == (inputs.root / "test-only.png").read_bytes()


@pytest.mark.parametrize(
    "path",
    ["../escape.png", "/tmp/escape.png", "C:/escape.png", "..\\escape.png", "out.jpg", ".", ""],
)
def test_output_path_safety(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, path: str
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    with pytest.raises(GraphicsError, match="output path"):
        save_png(card, inputs.root / "output", path)
    assert not (inputs.root / "output").exists()


def test_symlink_output_escape_and_source_overwrite(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    output = inputs.root / "output"
    output.mkdir()
    (output / "escape").symlink_to(inputs.root.parent, target_is_directory=True)
    with pytest.raises(GraphicsError, match="escapes output root"):
        save_png(card, output, "escape/out.png")
    with pytest.raises(GraphicsError, match="source flag asset"):
        save_png(card, inputs.root, "test-only.png", overwrite=True)


def test_existing_output_and_failed_write_preserve_previous(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    output_root = inputs.root / "output"
    output = save_png(card, output_root, "card.png")
    before = output.read_bytes()
    with pytest.raises(GraphicsError, match="already exists"):
        save_png(card, output_root, "card.png")
    with patch("quiztalcoatl.graphics.os.fsync", side_effect=OSError("disk failure")):
        with pytest.raises(GraphicsError, match="disk failure"):
            save_png(card, output_root, "card.png", overwrite=True)
    assert output.read_bytes() == before
    assert list(output_root.iterdir()) == [output]
    assert save_png(card, output_root, "card.png", overwrite=True).read_bytes() == before


def test_layout_invalid_ordinals_and_explicit_preview_status(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    with pytest.raises(GraphicsError, match="total_questions"):
        CardLayout(0)
    with pytest.raises(GraphicsError, match="preview_label"):
        CardLayout(15, "  ")
    question.ordinal = 16
    with pytest.raises(GraphicsError, match="ordinal"):
        render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    question.ordinal = 7
    card = render_card(question, CardLayout(15, "TEST ONLY"), content_root=inputs.root, fonts=fonts)
    assert next(block.text for block in card.text_blocks if block.role == "progress") == "07 / 15"
    assert (
        next(block.text for block in card.text_blocks if block.role == "preview-label")
        == "TEST ONLY"
    )
    assert "human design UAT pending" in card.design_status
    assert not any(
        block.role in {"brand-status", "mascot-placeholder"} for block in card.text_blocks
    )


def test_palette_contrast_baseline() -> None:
    for foreground, background in [
        (WHITE, BACKGROUND),
        (WHITE, SURFACE),
        (GOLD, TEAL),
        (GOLD, INK),
    ]:
        assert contrast_ratio(foreground, background) > 4.5


def test_dangling_output_symlink_and_hardlink_asset_are_rejected(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    output_root = inputs.root / "output"
    output_root.mkdir()
    (output_root / "dangling.png").symlink_to(output_root / "target.png")
    for overwrite in (False, True):
        with pytest.raises(GraphicsError, match="symlink"):
            save_png(card, output_root, "dangling.png", overwrite=overwrite)
    assert not (output_root / "target.png").exists()
    (output_root / "alias.png").hardlink_to(inputs.root / "test-only.png")
    with pytest.raises(GraphicsError, match="source flag asset"):
        save_png(card, output_root, "alias.png", overwrite=True)


def test_non_directory_output_root_has_actionable_error(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    blocked = inputs.root / "blocked"
    blocked.write_bytes(b"not a directory")
    with pytest.raises(GraphicsError, match="Cannot save PNG"):
        save_png(card, blocked, "card.png")
    assert blocked.read_bytes() == b"not a directory"


def test_two_by_two_answer_geometry_and_progress_pips(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    question.ordinal = 7
    card = render_card(question, CardLayout(15), content_root=inputs.root, fonts=fonts)
    blocks = {block.role: block for block in card.text_blocks}
    assert blocks["option-0"].box.y == blocks["option-1"].box.y
    assert blocks["option-2"].box.y == blocks["option-3"].box.y
    assert blocks["option-0"].box.y < blocks["option-2"].box.y
    assert blocks["option-0"].box.x < blocks["option-1"].box.x
    # The current pip and completed/remaining pips are three distinct real fills.
    assert card.image.getpixel((928, 96)) == (255, 212, 91)
    assert card.image.getpixel((740, 96)) != card.image.getpixel((1184, 96))


def test_explicit_transparent_brand_art_proportions_and_source_safety(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet
) -> None:
    brand = inputs.root / "synthetic-brand.png"
    artwork = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
    ImageDraw.Draw(artwork).rectangle((100, 50, 300, 250), fill=(255, 90, 20, 255))
    artwork.save(brand)
    before = brand.read_bytes()
    card = render_card(
        question, CardLayout(15), content_root=inputs.root, fonts=fonts, brand_asset=brand
    )
    assert card.brand_box is not None
    box = card.brand_box
    assert Box(1270, 264, 560, 470).contains(box)
    assert box.width * 3 == box.height * 4
    assert card.image.getpixel((box.x + box.width // 2, box.y + box.height // 2)) == (255, 90, 20)
    assert card.image.getpixel((box.x + 2, box.y + 2)) != (255, 90, 20)
    assert brand.read_bytes() == before
    with pytest.raises(GraphicsError, match="brand asset"):
        save_png(card, inputs.root, brand.name, overwrite=True)


@pytest.mark.parametrize("kind", ["missing", "corrupt", "rgb", "opaque-rgba", "invisible"])
def test_bad_brand_asset_is_actionable(
    inputs: SyntheticInputs, question: ResolvedQuestion, fonts: FontSet, kind: str
) -> None:
    brand = inputs.root / "brand.png"
    if kind == "corrupt":
        brand.write_bytes(b"bad PNG")
    elif kind == "rgb":
        Image.new("RGB", (10, 10), "white").save(brand)
    elif kind == "opaque-rgba":
        Image.new("RGBA", (10, 10), (255, 255, 255, 255)).save(brand)
    elif kind == "invisible":
        Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(brand)
    with pytest.raises(GraphicsError, match="brand asset"):
        render_card(
            question, CardLayout(15), content_root=inputs.root, fonts=fonts, brand_asset=brand
        )
