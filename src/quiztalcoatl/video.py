"""Publication-gated static-card orchestration and deterministic FFmpeg encoding."""

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from quiztalcoatl.content import ContentError, load_contract, load_snapshot
from quiztalcoatl.graphics import (
    BACKGROUND,
    GOLD,
    INK,
    WHITE,
    Box,
    CardLayout,
    FontSet,
    TextBlock,
    _brand,
    _text,
    load_fonts,
    render_card,
)
from quiztalcoatl.models import ResolvedQuizManifest
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.timeline import Segment, Timeline, build_timeline


@dataclass(frozen=True)
class Scene:
    path: Path
    duration_frames: int
    countdown: bool = False


@dataclass(frozen=True)
class RenderReport:
    output: Path
    frames: int
    output_bytes: int
    wall_seconds: float
    temporary_bytes: int
    preset: str
    warnings: tuple[str, ...] = ()


def _run(command: list[str], *, timeout: float = 180) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(command, capture_output=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace")[-12000:]
        raise ContentError(f"{command[0]} failed (exit {exc.returncode}):\n{detail}") from exc
    except subprocess.TimeoutExpired as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="replace")[-12000:]
        raise ContentError(f"{command[0]} timed out after {timeout}s: {detail}") from exc
    except OSError as exc:
        raise ContentError(f"Cannot execute {command[0]}: {exc}") from exc


def _branded_scene(
    segment: Segment, fonts: FontSet, brand: Path, preview_label: str | None = None
) -> Image.Image:
    image = Image.new("RGB", (1920, 1080), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 440), (1200, 160), (1920, 1080), (0, 1080)], fill="#0C363A")
    draw.rectangle((0, 0, 1920, 360), fill=BACKGROUND)
    blocks: list[TextBlock] = []
    if segment.kind == "intro":
        title, lines = "15 FLAGS. ONE CHALLENGE.", "Choose A, B, C or D.\nKeep score as you go."
    elif segment.kind == "checkpoint":
        assert segment.question is not None
        title = f"{segment.question.ordinal} DOWN. HOW MANY RIGHT?"
        lines = "Keep your score.\nThe next round starts now."
    else:
        title, lines = (
            "WHAT'S YOUR FINAL SCORE?",
            "Tell us how you did.\nKeep exploring with QUIZtalcoatl.",
        )
    _text(
        draw,
        blocks,
        fonts,
        "scene-title",
        title,
        Box(72, 150, 1776, 160),
        size=80,
        minimum=58,
        max_lines=2,
        bold=True,
        align="center",
        color=GOLD,
    )
    _text(
        draw,
        blocks,
        fonts,
        "scene-body",
        lines,
        Box(130, 440, 1020, 300),
        size=57,
        minimum=44,
        max_lines=3,
        bold=True,
        color=WHITE,
        background="#0C363A",
    )
    artwork = _brand(brand)
    artwork.thumbnail((540, 540), Image.Resampling.LANCZOS)
    image.paste(artwork, (1250, 380), artwork)
    if preview_label:
        _text(
            draw,
            blocks,
            fonts,
            "preview-label",
            preview_label,
            Box(72, 1030, 1776, 28),
            size=18,
            align="center",
        )
    return image


def _prepare_scenes(
    timeline: Timeline,
    work: Path,
    root: Path,
    fonts: FontSet,
    brand: Path,
    preview_label: str | None = None,
) -> list[Scene]:
    result: list[Scene] = []
    for segment in timeline.segments:
        if segment.kind in {"question", "reveal"}:
            assert segment.question is not None
            image = render_card(
                segment.question,
                CardLayout(15, preview_label),
                content_root=root,
                fonts=fonts,
                reveal=segment.kind == "reveal",
                brand_asset=brand,
            ).image
        else:
            image = _branded_scene(segment, fonts, brand, preview_label)
        path = work / f"scene-{segment.sequence:03}.png"
        image.save(path, format="PNG")
        result.append(Scene(path, segment.duration_frames, segment.kind == "question"))
    for index in range(14):
        timer = Image.new("RGBA", (224, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(timer)
        draw.rounded_rectangle((0, 0, 223, 59), radius=22, fill=GOLD)
        _text(
            draw,
            [],
            fonts,
            "countdown",
            f"{14 - index:02}s",
            Box(10, 6, 204, 48),
            size=35,
            bold=True,
            color=INK,
            background=GOLD,
            align="center",
        )
        timer.save(work / f"timer-{index:02}.png", format="PNG")
    return result


def ffmpeg_command(scene: Scene, destination: Path, work: Path, *, preset: str) -> list[str]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-nostdin",
        "-y",
        "-threads",
        "2",
        "-filter_threads",
        "1",
        "-filter_complex_threads",
        "1",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(scene.path),
    ]
    if scene.countdown:
        command += [
            "-framerate",
            "1",
            "-start_number",
            "0",
            "-i",
            str(work / "timer-%02d.png"),
            "-filter_complex",
            "[0:v][1:v]overlay=1300:72:eof_action=repeat:shortest=0,fps=30[v]",
            "-map",
            "[v]",
        ]
    else:
        command += ["-map", "0:v:0"]
    return command + [
        "-an",
        "-frames:v",
        str(scene.duration_frames),
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-tune",
        "stillimage",
        "-crf",
        "20",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-fps_mode",
        "cfr",
        "-map_metadata",
        "-1",
        "-fflags",
        "+bitexact",
        "-flags:v",
        "+bitexact",
        str(destination),
    ]


def _encode_sequence(
    scenes: list[Scene], work: Path, destination: Path, *, preset: str
) -> tuple[str, ...]:
    if not scenes or any(scene.duration_frames <= 0 for scene in scenes):
        raise ContentError("encoding requires positive-duration scenes")
    parts = []
    warnings: list[str] = []
    for index, scene in enumerate(scenes):
        part = work / f"part-{index:03}.mp4"
        result = _run(
            ffmpeg_command(scene, part, work, preset=preset),
            timeout=max(120, scene.duration_frames / 30 * 30),
        )
        if result.stderr.strip():
            warnings.append(result.stderr.decode("utf-8", errors="replace"))
        parts.append(f"file '{part.name}'\n")
    concat = work / "concat.txt"
    concat.write_text("".join(parts), encoding="ascii")
    result = _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-nostdin",
            "-y",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            str(concat),
            "-map",
            "0:v:0",
            "-c",
            "copy",
            "-an",
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )

    if result.stderr.strip():
        warnings.append(result.stderr.decode("utf-8", errors="replace"))
    return tuple(warnings)


def probe_video(path: Path, *, expected_frames: int) -> dict[str, Any]:
    """Decode/count the actual video and enforce the initial video-only 1080p contract."""
    raw = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        timeout=max(180, expected_frames / 30 * 3),
    )
    try:
        metadata: dict[str, Any] = json.loads(raw.stdout)
        if not isinstance(metadata, dict):
            raise ContentError("ffprobe returned an invalid metadata object")
        streams = metadata.get("streams", [])
        if not isinstance(streams, list) or len(streams) != 1 or not isinstance(streams[0], dict):
            raise ContentError("encoded output must contain exactly one video stream and no audio")
        video = streams[0]
        expected = {
            "codec_type": "video",
            "codec_name": "h264",
            "pix_fmt": "yuv420p",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
        }
        if any(video.get(key) != value for key, value in expected.items()):
            raise ContentError(
                "encoded output has unexpected codec, dimensions, pixel format or frame rate"
            )
        if int(video.get("nb_read_frames", -1)) != expected_frames:
            raise ContentError("encoded output decoded frame count does not match timeline")
        duration = float(metadata["format"]["duration"])
        if not math.isfinite(duration) or abs(duration - expected_frames / 30) > 1 / 30:
            raise ContentError("encoded output duration does not match timeline")
        if path.stat().st_size <= 0:
            raise ContentError("encoded video is empty")
        return metadata
    except (KeyError, TypeError, ValueError, OSError) as exc:
        if isinstance(exc, ContentError):
            raise
        raise ContentError(f"Cannot validate encoded output metadata: {exc}") from exc


def _protect_output(output: Path, sources: list[Path], *, overwrite: bool) -> None:
    if output.is_symlink() or output.is_dir():
        raise ContentError("video output must not be a symlink or directory")
    destination = output.resolve()
    for source in sources:
        if destination == source.resolve() or (
            output.exists() and source.exists() and output.samefile(source)
        ):
            raise ContentError(f"video output must not replace an input, asset or font: {output}")
    if output.exists() and not overwrite:
        raise ContentError("video output already exists; supply --overwrite explicitly")
    if output.suffix.lower() != ".mp4":
        raise ContentError("video output must use an .mp4 extension")


def render_video(
    countries_path: Path,
    recipe_path: Path,
    manifest_path: Path,
    output: Path,
    *,
    content_root: Path | None = None,
    font_dir: Path | None = None,
    brand_asset: Path | None = None,
    overwrite: bool = False,
    preset: str = "veryfast",
    preview_label: str | None = None,
) -> RenderReport:
    """Require genuine publication readiness and exact fresh resolution before any output."""
    started = time.perf_counter()
    if preset not in {"ultrafast", "veryfast", "medium"}:
        raise ContentError("supported encoding presets: ultrafast, veryfast, medium")
    fresh = resolve_files(countries_path, recipe_path, content_root=content_root)
    manifest_bytes = manifest_path.read_bytes()
    supplied = load_contract(manifest_path, ResolvedQuizManifest)
    if manifest_path.read_bytes() != manifest_bytes:
        raise ContentError("manifest changed during loading")
    if supplied != fresh:
        raise ContentError(
            "supplied manifest is stale or modified; regenerate it from these exact inputs"
        )
    root = content_root if content_root is not None else countries_path.resolve().parent
    timeline = build_timeline(supplied, content_root=root)
    font_root_value = font_dir if font_dir is not None else os.environ.get("QUIZTALCOATL_FONT_DIR")
    fonts = load_fonts(Path(font_root_value) if font_root_value else None)
    assert font_root_value is not None
    font_root = Path(font_root_value)
    brand = brand_asset if brand_asset is not None else root / "assets/brand/quiztalcoatl-logo.png"
    _brand(brand)
    snapshot = load_snapshot(countries_path)
    sources = [
        countries_path,
        recipe_path,
        manifest_path,
        brand,
        font_root / "DejaVuSans.ttf",
        font_root / "DejaVuSans-Bold.ttf",
    ]
    sources += [
        root / asset.path
        for country in snapshot.countries
        for asset in (country.flag, country.outline)
        if asset is not None
    ]
    _protect_output(output, sources, overwrite=overwrite)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ContentError("FFmpeg and ffprobe are required; install FFmpeg with libx264 support")
    # Retain hashes to detect ordinary concurrent edits before final publication.
    original = {
        source: hashlib.sha256(source.read_bytes()).digest()
        for source in sources
        if source.is_file()
    }
    if (
        hashlib.sha256(countries_path.read_bytes()).hexdigest() != fresh.snapshot_sha256
        or hashlib.sha256(recipe_path.read_bytes()).hexdigest() != fresh.recipe_sha256
        or manifest_path.read_bytes() != manifest_bytes
    ):
        raise ContentError("source inputs changed since resolution")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".quiztalcoatl-render-", dir=output.parent
    ) as directory:
        work = Path(directory)
        scenes = _prepare_scenes(timeline, work, root, fonts, brand, preview_label)
        encoded = work / "complete.mp4"
        warnings = _encode_sequence(scenes, work, encoded, preset=preset)
        probe_video(encoded, expected_frames=timeline.total_frames)
        if any(
            hashlib.sha256(source.read_bytes()).digest() != digest
            for source, digest in original.items()
        ):
            raise ContentError("a render input changed during encoding; output was not published")
        temporary_bytes = sum(path.stat().st_size for path in work.iterdir() if path.is_file())
        size = encoded.stat().st_size
        if overwrite:
            os.replace(encoded, output)
        else:
            os.link(encoded, output)
    return RenderReport(
        output,
        timeline.total_frames,
        size,
        time.perf_counter() - started,
        temporary_bytes,
        preset,
        warnings,
    )
