"""Measured thumbnail geometry and actual PNG behavior; no visual approval implied."""

import hashlib
import io
from pathlib import Path

import pytest
from PIL import Image, ImageFont
from test_resolver import SyntheticInputs
from test_resolver import inputs as inputs

from quiztalcoatl.graphics import Box, FontSet, GraphicsError, contrast_ratio
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.thumbnail import RenderedThumbnail, encode_thumbnail, render_thumbnail

BRAND = Path(__file__).resolve().parents[1] / "assets/brand/quiztalcoatl-logo.png"


@pytest.fixture
def fonts() -> FontSet:
    regular = ImageFont.load_default(size=40)
    assert isinstance(regular, ImageFont.FreeTypeFont)
    return FontSet(regular, regular.font_variant(size=40))


def draw(
    inputs: SyntheticInputs, fonts: FontSet, hook: str = "NAME THESE FLAGS"
) -> RenderedThumbnail:
    return render_thumbnail(
        resolve_files(inputs.countries_path, inputs.recipe_path).questions,
        hook=hook,
        question_count=15,
        content_root=inputs.root,
        fonts=fonts,
        brand_asset=BRAND,
    )


def test_actual_png_brand_and_small_geometry(inputs: SyntheticInputs, fonts: FontSet) -> None:
    original = BRAND.read_bytes()
    thumbnail = draw(inputs, fonts)
    payload = encode_thumbnail(thumbnail)
    with Image.open(io.BytesIO(payload)) as image:
        assert image.size == (1280, 720) and image.format == "PNG" and image.mode == "RGB"
        mobile = image.resize((320, 180), Image.Resampling.LANCZOS)
        assert mobile.getbbox() == (0, 0, 320, 180)
    assert len(payload) < 2_000_000
    assert BRAND.read_bytes() == original
    assert thumbnail.brand_source_size == Image.open(BRAND).size
    box = thumbnail.brand_box
    assert (
        abs(
            box.width / box.height - thumbnail.brand_source_size[0] / thumbnail.brand_source_size[1]
        )
        < 0.01
    )
    assert box.width >= 400
    # Actual supplied logo differs visibly from the empty dark hero background.
    assert len(thumbnail.image.crop(box.bounds).getcolors(maxcolors=1_000_000) or []) > 1000
    safe = Box(40, 40, 1200, 656)
    for block in thumbnail.text_blocks:
        assert safe.contains(block.box)
        assert all(block.box.contains(ink) for ink in block.ink_boxes)
        assert contrast_ratio(block.foreground, block.background) >= 4.5
        if block.role == "hook":
            assert block.size / 4 >= 16  # 320 px review: a measured minimum, not human OCR/UAT.
            assert all(ink.height / 4 >= 10 for ink in block.ink_boxes)


def test_deterministic_controlled_png(inputs: SyntheticInputs, fonts: FontSet) -> None:
    first, second = encode_thumbnail(draw(inputs, fonts)), encode_thumbnail(draw(inputs, fonts))
    assert hashlib.sha256(first).digest() == hashlib.sha256(second).digest()


@pytest.mark.parametrize("size", [(1200, 800), (900, 900), (1600, 400), (400, 800)])
def test_flags_keep_original_proportions(
    inputs: SyntheticInputs, fonts: FontSet, size: tuple[int, int]
) -> None:
    path = inputs.root / "test-only.png"
    Image.new("RGB", size, "red").save(path)
    data = inputs.countries_path.read_text()
    flag = inputs.snapshot.countries[0].flag
    assert flag is not None
    data = data.replace(
        flag.sha256,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    inputs.countries_path.write_text(data)
    thumbnail = draw(inputs, fonts)
    for box, source in zip(thumbnail.flag_boxes, thumbnail.flag_source_sizes, strict=True):
        assert abs(box.width / box.height - source[0] / source[1]) < 0.025


@pytest.mark.parametrize("hook", ["", "X" * 121, "unbreakable" * 10])
def test_impossible_hook_fails_explicitly(
    inputs: SyntheticInputs, fonts: FontSet, hook: str
) -> None:
    with pytest.raises(GraphicsError, match="hook|fit"):
        draw(inputs, fonts, hook)


def test_current_hook_fits_readable_floor(inputs: SyntheticInputs, fonts: FontSet) -> None:
    thumbnail = draw(inputs, fonts, "How many flags can you name?")
    assert next(b.size for b in thumbnail.text_blocks if b.role == "hook") >= 64


@pytest.mark.parametrize("kind", ["missing", "corrupt", "opaque"])
def test_invalid_brand(inputs: SyntheticInputs, fonts: FontSet, kind: str) -> None:
    brand = inputs.root / "brand.png"
    if kind == "corrupt":
        brand.write_bytes(b"not png")
    elif kind == "opaque":
        Image.new("RGB", (50, 50), "white").save(brand)
    with pytest.raises(GraphicsError, match="brand"):
        render_thumbnail(
            resolve_files(inputs.countries_path, inputs.recipe_path).questions,
            hook="NAME THESE FLAGS",
            question_count=15,
            content_root=inputs.root,
            fonts=fonts,
            brand_asset=brand,
        )
