"""Minimal command-line interface and local prerequisite checks."""

import platform
import shutil
import subprocess
from importlib.metadata import version
from typing import Annotated

import typer

app = typer.Typer(
    name="quiztalcoatl",
    help="QUIZtalcoatl: local-first geography quiz video production.",
    no_args_is_help=True,
    add_completion=False,
)


def show_version(value: bool) -> None:
    if value:
        typer.echo(f"QUIZtalcoatl {version('quiztalcoatl')}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=show_version, is_eager=True, help="Show package version."
        ),
    ] = False,
) -> None:
    """Run the requested command."""


def check_executable(name: str) -> bool:
    executable = shutil.which(name)
    if executable is None:
        typer.echo(f"{name}: not found on PATH")
        return False
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            errors="replace",
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        typer.echo(f"{name}: could not run {executable}: {exc}")
        return False
    lines = result.stdout.strip().splitlines()
    typer.echo(f"{name}: {lines[0] if lines else 'available (no version output)'}")
    return True


@app.command()
def doctor() -> None:
    """Check Python, FFmpeg and ffprobe without network access."""
    typer.echo(f"Python: {platform.python_version()}")
    results = [check_executable(name) for name in ("ffmpeg", "ffprobe")]
    if not all(results):
        typer.echo(
            "Install or repair FFmpeg (including ffprobe), and ensure both are on PATH.\n"
            "macOS: brew install ffmpeg\n"
            "Ubuntu/Debian: sudo apt-get update && sudo apt-get install ffmpeg\n"
            "See README.md for prerequisites, then rerun quiztalcoatl doctor."
        )
        raise typer.Exit(code=1)
