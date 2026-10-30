"""Gated renderer units plus a real decoded 1080p media integration sequence."""

import io
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
from test_resolver import SyntheticInputs
from test_resolver import inputs as inputs
from typer.testing import CliRunner

from quiztalcoatl.cli import app
from quiztalcoatl.content import ContentError
from quiztalcoatl.graphics import BACKGROUND, load_fonts
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.timeline import build_timeline
from quiztalcoatl.video import (
    Scene,
    _encode_sequence,
    _prepare_scenes,
    _run,
    ffmpeg_command,
    probe_video,
    render_video,
)


@pytest.fixture
def render_inputs(inputs: SyntheticInputs) -> tuple[Path, Path, Path]:
    manifest = inputs.root / "manifest.json"
    manifest.write_text(resolve_files(inputs.countries_path, inputs.recipe_path).model_dump_json())
    fonts = inputs.root / "fonts"
    fonts.mkdir()
    embedded = ImageFont.load_default(size=40)
    assert isinstance(embedded, ImageFont.FreeTypeFont) and isinstance(embedded.path, io.BytesIO)
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        (fonts / name).write_bytes(embedded.path.getvalue())
    brand = inputs.root / "brand.png"
    art = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(art).ellipse((5, 5, 95, 95), fill="gold")
    art.save(brand)
    return manifest, fonts, brand


def invoke_render(
    inputs: SyntheticInputs,
    files: tuple[Path, Path, Path],
    output: Path,
    *,
    overwrite: bool = False,
) -> Any:
    manifest, fonts, brand = files
    return render_video(
        inputs.countries_path,
        inputs.recipe_path,
        manifest,
        output,
        content_root=inputs.root,
        font_dir=fonts,
        brand_asset=brand,
        overwrite=overwrite,
    )


@pytest.mark.parametrize(
    "failure", ["draft", "unverified", "stale", "modified", "missing", "corrupt", "malformed"]
)
def test_invalid_inputs_do_not_create_output(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path], failure: str
) -> None:
    manifest, _, _ = render_inputs
    if failure in {"draft", "unverified"}:
        data = json.loads(inputs.countries_path.read_bytes())
        if failure == "draft":
            data["editorial_status"] = "draft"
        else:
            data["countries"][0]["verification"]["flag"]["status"] = "needs_verification"
        inputs.countries_path.write_text(json.dumps(data))
    elif failure in {"stale", "modified"}:
        data = json.loads(manifest.read_bytes())
        data["seed"] += 1
        if failure == "modified":
            data["questions"][0]["prompt"] = "A modified prompt"
        manifest.write_text(json.dumps(data))
    elif failure in {"missing", "corrupt"}:
        asset = inputs.root / "test-only.png"
        if failure == "missing":
            asset.unlink()
        else:
            asset.write_bytes(b"corrupt")
    else:
        manifest.write_text("{")
    output = inputs.root / "output/video.mp4"
    with pytest.raises(ValueError):
        invoke_render(inputs, render_inputs, output)
    assert not output.parent.exists()


@pytest.mark.parametrize(
    "target", ["snapshot", "recipe", "manifest", "asset", "brand", "font", "hardlink"]
)
def test_inputs_cannot_be_output(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path], target: str
) -> None:
    manifest, fonts, brand = render_inputs
    targets = {
        "snapshot": inputs.countries_path,
        "recipe": inputs.recipe_path,
        "manifest": manifest,
        "asset": inputs.root / "test-only.png",
        "brand": brand,
        "font": fonts / "DejaVuSans.ttf",
    }
    if target == "hardlink":
        output = inputs.root / "hardlink.mp4"
        os.link(manifest, output)
    else:
        output = targets[target]
    before = output.read_bytes()
    with pytest.raises(ContentError, match="must not replace"):
        invoke_render(inputs, render_inputs, output, overwrite=True)
    assert output.read_bytes() == before


def test_existing_output_and_failure_cleanup(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path]
) -> None:
    output = inputs.root / "video.mp4"
    output.write_bytes(b"previous output")
    with pytest.raises(ContentError, match="overwrite"):
        invoke_render(inputs, render_inputs, output)
    with patch("quiztalcoatl.video._prepare_scenes", side_effect=ContentError("drawing failed")):
        with pytest.raises(ContentError, match="drawing failed"):
            invoke_render(inputs, render_inputs, output, overwrite=True)
    assert output.read_bytes() == b"previous output"
    assert not list(inputs.root.glob(".quiztalcoatl-render-*"))


def test_encoding_failure_preserves_output_and_logs(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path]
) -> None:
    output = inputs.root / "video.mp4"
    output.write_bytes(b"keep")
    with (
        patch("quiztalcoatl.video._prepare_scenes", return_value=[]),
        patch(
            "quiztalcoatl.video._encode_sequence",
            side_effect=ContentError("libx264 failed: diagnostic"),
        ),
    ):
        with pytest.raises(ContentError, match="diagnostic"):
            invoke_render(inputs, render_inputs, output, overwrite=True)
    assert output.read_bytes() == b"keep" and not list(inputs.root.glob(".quiztalcoatl-render-*"))


@pytest.mark.parametrize(
    "error",
    [
        OSError("missing executable"),
        subprocess.TimeoutExpired("ffmpeg", 1),
        subprocess.CalledProcessError(1, "ffmpeg", stderr=b"useful encoder detail"),
    ],
)
def test_subprocess_errors_are_actionable(error: Exception) -> None:
    with patch("quiztalcoatl.video.subprocess.run", side_effect=error):
        with pytest.raises(ContentError, match="ffmpeg"):
            _run(["ffmpeg"])


def test_ffmpeg_arguments_are_explicit(tmp_path: Path) -> None:
    command = ffmpeg_command(
        Scene(tmp_path / "space in name.png", 60, True),
        tmp_path / "out.mp4",
        tmp_path,
        preset="veryfast",
    )
    assert command[0] == "ffmpeg"
    assert command[command.index("-frames:v") + 1] == "60"
    assert "libx264" in command and "yuv420p" in command
    assert "overlay=1300:72" in command[command.index("-filter_complex") + 1]
    assert str(tmp_path / "space in name.png") in command
    assert "-an" in command and "30" in command


def test_render_cli_help_and_real_draft_gate(tmp_path: Path) -> None:
    assert "render" in CliRunner().invoke(app, ["--help"]).output
    assert "--manifest" in CliRunner().invoke(app, ["render", "--help"]).output
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "output/video.mp4"
    result = CliRunner().invoke(
        app,
        [
            "render",
            "--countries",
            str(root / "data/countries.json"),
            "--recipe",
            str(root / "recipes/V-001.json"),
            "--manifest",
            str(tmp_path / "missing.json"),
            "--content-root",
            str(root),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 1 and "editorial approval" in result.output
    assert not output.parent.exists()


def test_mocked_success_is_atomic_and_inputs_unchanged(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path]
) -> None:
    sources = [
        inputs.countries_path,
        inputs.recipe_path,
        *render_inputs,
        inputs.root / "test-only.png",
    ]
    before = {path: path.read_bytes() for path in sources if path.is_file()}
    output = inputs.root / "output/video.mp4"

    def encode(scenes: list[Scene], work: Path, destination: Path, *, preset: str) -> None:
        destination.write_bytes(b"complete test video")

    with (
        patch("quiztalcoatl.video._prepare_scenes", return_value=[]),
        patch("quiztalcoatl.video._encode_sequence", side_effect=encode),
        patch("quiztalcoatl.video.probe_video", return_value={}),
    ):
        report = invoke_render(inputs, render_inputs, output)
    assert report.frames == 10650 and output.read_bytes() == b"complete test video"
    assert before == {path: path.read_bytes() for path in before}
    assert list(output.parent.iterdir()) == [output]


@pytest.mark.smoke
def test_real_question_countdown_reveal_checkpoint_video(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    manifest, font_dir, brand = render_inputs
    work = tmp_path / "media"
    work.mkdir()
    timeline = build_timeline(resolve_files(inputs.countries_path, inputs.recipe_path))
    # Production graphics/encoding/probing with short test durations.
    chosen = (timeline.segments[1], timeline.segments[2], timeline.segments[11])
    scenes = _prepare_scenes(timeline, work, inputs.root, load_fonts(font_dir), brand)
    selected = [
        Scene(scenes[1].path, 60, True),
        Scene(scenes[2].path, 30),
        Scene(scenes[11].path, 30),
    ]
    assert chosen[-1].kind == "checkpoint"
    output = work / "short.mp4"
    _encode_sequence(selected, work, output, preset="ultrafast")
    repeat = work / "repeat.mp4"
    _encode_sequence(selected, work, repeat, preset="ultrafast")
    assert output.read_bytes() == repeat.read_bytes()
    metadata = probe_video(output, expected_frames=120)
    assert metadata["streams"][0]["nb_read_frames"] == "120"
    frames = []
    for position in (0.2, 1.2, 2.2, 3.2):
        result = _run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(position),
                "-i",
                str(output),
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-c:v",
                "png",
                "pipe:1",
            ]
        )
        with Image.open(io.BytesIO(result.stdout)) as frame:
            frames.append(frame.convert("RGB"))
    expected_timers = []
    for number in (0, 1):
        expected = Image.new("RGB", (224, 60), BACKGROUND)
        with Image.open(work / f"timer-{number:02}.png") as timer:
            expected.paste(timer, (0, 0), timer)
        expected_timers.append(expected)
    for index in (0, 1):
        actual = frames[index].crop((1300, 72, 1524, 132))
        distances = [
            sum(ImageStat.Stat(ImageChops.difference(actual, expected)).mean)
            for expected in expected_timers
        ]
        assert distances[index] < distances[1 - index]
    index = (
        timeline.segments[1].question.correct_answer_index if timeline.segments[1].question else 0
    )
    x, y = 72 + index % 2 * 910 + 836, 764 + index // 2 * 132 + 56
    pixel = frames[2].getpixel((x, y))
    assert isinstance(pixel, tuple)
    assert sum(abs(a - b) for a, b in zip(pixel, (255, 212, 91), strict=True)) < 18
    assert frames[3].tobytes() != frames[2].tobytes()
    assert frames[0].size == (1920, 1080) and output.stat().st_size > 0


@pytest.mark.parametrize("raw", [b"{", b"[]", b"{}", b'{"streams":[{}]}'])
def test_invalid_probe_metadata_is_actionable(tmp_path: Path, raw: bytes) -> None:
    with patch(
        "quiztalcoatl.video._run", return_value=subprocess.CompletedProcess([], 0, raw, b"")
    ):
        with pytest.raises(ContentError):
            probe_video(tmp_path / "video.mp4", expected_frames=120)


def test_probe_failure_and_concurrent_input_edit_prevent_publication(
    inputs: SyntheticInputs, render_inputs: tuple[Path, Path, Path]
) -> None:
    output = inputs.root / "video.mp4"
    output.write_bytes(b"previous")

    def encode(
        scenes: list[Scene], work: Path, destination: Path, *, preset: str
    ) -> tuple[str, ...]:
        destination.write_bytes(b"encoded")
        return ()

    with (
        patch("quiztalcoatl.video._prepare_scenes", return_value=[]),
        patch("quiztalcoatl.video._encode_sequence", side_effect=encode),
        patch("quiztalcoatl.video.probe_video", side_effect=ContentError("wrong frame count")),
    ):
        with pytest.raises(ContentError, match="frame count"):
            invoke_render(inputs, render_inputs, output, overwrite=True)
    assert output.read_bytes() == b"previous"

    def edit(scenes: list[Scene], work: Path, destination: Path, *, preset: str) -> tuple[str, ...]:
        destination.write_bytes(b"encoded")
        inputs.recipe_path.write_bytes(inputs.recipe_path.read_bytes() + b"\n")
        return ()

    with (
        patch("quiztalcoatl.video._prepare_scenes", return_value=[]),
        patch("quiztalcoatl.video._encode_sequence", side_effect=edit),
        patch("quiztalcoatl.video.probe_video", return_value={}),
    ):
        with pytest.raises(ContentError, match="input changed"):
            invoke_render(inputs, render_inputs, output, overwrite=True)
    assert output.read_bytes() == b"previous"
    assert not list(inputs.root.glob(".quiztalcoatl-render-*"))


def test_timeout_keeps_available_stderr() -> None:
    error = subprocess.TimeoutExpired("ffmpeg", 1, stderr=b"available encoder context")
    with patch("quiztalcoatl.video.subprocess.run", side_effect=error):
        with pytest.raises(ContentError, match="available encoder context"):
            _run(["ffmpeg"])
