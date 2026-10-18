"""Real media-tool integration; outputs live only in pytest's temporary directory."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_ffmpeg_smoke(tmp_path: Path) -> None:
    for executable in ("ffmpeg", "ffprobe"):
        assert shutil.which(executable), (
            f"{executable} is missing. Install FFmpeg with H.264/libx264 support and ffprobe "
            "and add both to PATH; see README.md."
        )
    output = tmp_path / "smoke.mp4"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=320x180:rate=30",
                "-t",
                "2",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except subprocess.CalledProcessError as exc:
        pytest.fail(f"Media tool failed: {exc}\n{exc.stderr}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.fail(f"Cannot run media tools: {exc}. Check your FFmpeg installation.")

    metadata = json.loads(probe.stdout)
    video_streams = [s for s in metadata["streams"] if s["codec_type"] == "video"]
    assert len(video_streams) == 1
    stream = video_streams[0]
    assert (stream["width"], stream["height"]) == (320, 180)
    assert stream["codec_name"] == "h264"
    assert stream["pix_fmt"] == "yuv420p"
    assert stream["r_frame_rate"] == "30/1"
    assert 1.8 <= float(metadata["format"]["duration"]) <= 2.2
    assert output.stat().st_size > 0
