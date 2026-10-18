"""CLI tests independent of installed media tools."""

import platform
import subprocess
import sys
from importlib.metadata import version
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from quiztalcoatl.cli import app


def test_help() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "QUIZtalcoatl" in result.stdout
    assert "doctor" in result.stdout


def test_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"QUIZtalcoatl {version('quiztalcoatl')}"


def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "quiztalcoatl", "--help"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert "QUIZtalcoatl" in result.stdout
    assert "doctor" in result.stdout


def test_doctor_success() -> None:
    with (
        patch("quiztalcoatl.cli.shutil.which", side_effect=["/bin/ffmpeg", "/bin/ffprobe"]),
        patch(
            "quiztalcoatl.cli.subprocess.run",
            side_effect=[
                subprocess.CompletedProcess([], 0, "ffmpeg version test\nmore details"),
                subprocess.CompletedProcess([], 0, "ffprobe version test\nmore details"),
            ],
        ) as run,
    ):
        result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert f"Python: {platform.python_version()}" in result.stdout
    assert "ffmpeg version test" in result.stdout
    assert "ffprobe version test" in result.stdout
    assert "more details" not in result.stdout
    assert run.call_count == 2
    assert run.call_args_list[0].args[0] == ["/bin/ffmpeg", "-version"]


@pytest.mark.parametrize("missing", ["ffmpeg", "ffprobe"])
def test_doctor_missing_dependency(missing: str) -> None:
    with (
        patch(
            "quiztalcoatl.cli.shutil.which",
            side_effect=lambda name: None if name == missing else f"/bin/{name}",
        ),
        patch(
            "quiztalcoatl.cli.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, "version test"),
        ) as run,
    ):
        result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert f"{missing}: not found on PATH" in result.stdout
    assert "brew install ffmpeg" in result.stdout
    assert "sudo apt-get install ffmpeg" in result.stdout
    assert run.call_count == 1


@pytest.mark.parametrize(
    "error",
    [
        OSError("cannot execute"),
        subprocess.CalledProcessError(1, "ffmpeg"),
        subprocess.TimeoutExpired("ffmpeg", 10),
    ],
)
def test_doctor_executable_error(error: Exception) -> None:
    with (
        patch("quiztalcoatl.cli.shutil.which", return_value="/bin/tool"),
        patch("quiztalcoatl.cli.subprocess.run", side_effect=error) as run,
    ):
        result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "could not run" in result.stdout
    assert "Install or repair FFmpeg" in result.stdout
    assert run.call_count == 2


def test_doctor_empty_version_output() -> None:
    with (
        patch("quiztalcoatl.cli.shutil.which", return_value="/bin/tool"),
        patch(
            "quiztalcoatl.cli.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, ""),
        ),
    ):
        result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "available (no version output)" in result.stdout
