"""Minimal command-line interface and local prerequisite checks."""

import os
import platform
import shutil
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from quiztalcoatl.content import ContentError, load_recipe, load_snapshot, validate_inputs
from quiztalcoatl.models import ResolvedQuizManifest
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.video import render_video

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


@app.command()
def validate(
    countries: Annotated[Path, typer.Option(help="Local country snapshot JSON.")],
    recipe: Annotated[Path, typer.Option(help="Local quiz recipe JSON.")],
    publication_ready: Annotated[
        bool, typer.Option(help="Require editorial approval, verified facts and production assets.")
    ] = False,
    content_root: Annotated[
        Path | None,
        typer.Option(help="Root for asset paths; defaults to the country snapshot directory."),
    ] = None,
) -> None:
    """Validate local inputs without changing files or accessing external services."""
    try:
        snapshot = load_snapshot(countries)
        quiz_recipe = load_recipe(recipe)
        validate_inputs(
            snapshot,
            quiz_recipe,
            content_root if content_root is not None else countries.resolve().parent,
            publication_ready=publication_ready,
        )
    except ContentError as exc:
        typer.echo(f"Validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    mode = "publication readiness" if publication_ready else "structural validity (not approval)"
    typer.echo(f"Validation succeeded: {mode} for {quiz_recipe.video_id} / {snapshot.snapshot_id}.")


def _protect_inputs(
    output: Path,
    countries: Path,
    recipe: Path,
    content_root: Path | None,
    manifest: ResolvedQuizManifest,
) -> None:
    root = content_root if content_root is not None else countries.resolve().parent
    protected = [countries, recipe]
    # Include unselected assets as well as the flags resolved into this manifest.
    snapshot = load_snapshot(countries)
    for country in snapshot.countries:
        protected.extend(root / asset.path for asset in (country.flag, country.outline) if asset)
    protected.extend(root / question.asset.path for question in manifest.questions)
    destination = output.resolve()
    for source in protected:
        if destination == source.resolve() or (
            output.exists() and source.exists() and output.samefile(source)
        ):
            raise ContentError(f"output must not replace an input JSON file or asset: {output}")


def _write_manifest(output: Path, serialized: str, *, overwrite: bool) -> None:
    if output.is_dir():
        raise ContentError(f"output is a directory: {output}")
    if not overwrite and (output.exists() or output.is_symlink()):
        raise ContentError(f"output already exists: {output}; supply --overwrite to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, output)
        else:
            # Atomic creation refuses a destination that appeared after the existence check.
            try:
                os.link(temporary, output)
            except FileExistsError as exc:
                raise ContentError(
                    f"output already exists: {output}; supply --overwrite to replace it"
                ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@app.command()
def resolve(
    countries: Annotated[Path, typer.Option(help="Local country snapshot JSON.")],
    recipe: Annotated[Path, typer.Option(help="Local quiz recipe JSON.")],
    output: Annotated[
        Path, typer.Option(help="Explicit destination for the resolved manifest JSON.")
    ],
    content_root: Annotated[
        Path | None,
        typer.Option(help="Root for asset paths; defaults to the country snapshot directory."),
    ] = None,
    overwrite: Annotated[
        bool, typer.Option(help="Replace an existing output after validation.")
    ] = False,
) -> None:
    """Resolve publication-ready inputs and atomically write a deterministic manifest."""
    try:
        manifest = resolve_files(countries, recipe, content_root=content_root)
        serialized = manifest.model_dump_json(indent=2) + "\n"
        _protect_inputs(output, countries, recipe, content_root, manifest)
        _write_manifest(output, serialized, overwrite=overwrite)
    except (OSError, ValueError) as exc:
        typer.echo(f"Resolution failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Resolved {manifest.video_id}: {len(manifest.questions)} questions, "
        f"{manifest.expected_total_seconds:g} seconds -> {output}"
    )


@app.command()
def render(
    countries: Annotated[Path, typer.Option(help="Publication-ready country snapshot JSON.")],
    recipe: Annotated[Path, typer.Option(help="Approved V-001 recipe JSON.")],
    manifest: Annotated[Path, typer.Option(help="Exact current resolved manifest JSON.")],
    output: Annotated[Path, typer.Option(help="Explicit MP4 destination.")],
    content_root: Annotated[
        Path | None, typer.Option(help="Repository-relative asset root.")
    ] = None,
    font_dir: Annotated[
        Path | None,
        typer.Option(help="Explicit DejaVu directory; otherwise use QUIZTALCOATL_FONT_DIR."),
    ] = None,
    brand_asset: Annotated[
        Path | None,
        typer.Option(help="Transparent channel artwork; defaults to content-root assets/brand."),
    ] = None,
    overwrite: Annotated[
        bool, typer.Option(help="Replace an existing MP4 after all validation.")
    ] = False,
) -> None:
    """Render publication-ready V-001 inputs to a verified 355-second silent MP4."""
    try:
        report = render_video(
            countries,
            recipe,
            manifest,
            output,
            content_root=content_root,
            font_dir=font_dir,
            brand_asset=brand_asset,
            overwrite=overwrite,
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"Rendering failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Rendered V-001: {report.frames} frames / 355 seconds / "
        f"{report.output_bytes} bytes in {report.wall_seconds:.1f}s -> {output}"
    )
