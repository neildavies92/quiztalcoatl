"""Fresh approval gates, deterministic metadata and failure-safe coexisting outputs."""

import hashlib
import json
import os
import socket
from pathlib import Path
from unittest.mock import patch

import pytest
from test_resolver import SyntheticInputs
from test_resolver import inputs as inputs
from test_thumbnail import BRAND
from test_thumbnail import fonts as fonts

from quiztalcoatl.graphics import FontSet
from quiztalcoatl.models import ResolvedQuestion
from quiztalcoatl.publication import (
    OWNED_FILES,
    PublicationError,
    PublicationMetadata,
    generate_package,
)
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.thumbnail import RenderedThumbnail, render_thumbnail


def package(
    inputs: SyntheticInputs,
    fonts: FontSet,
    *,
    overwrite: bool = False,
    manifest: Path | None = None,
    output: Path | None = None,
) -> PublicationMetadata:
    manifest_path = manifest or inputs.root / "manifest.json"
    if manifest is None and not manifest_path.exists():
        manifest_path.write_text(
            resolve_files(inputs.countries_path, inputs.recipe_path).model_dump_json(indent=2)
        )
    return generate_package(
        inputs.countries_path,
        inputs.recipe_path,
        manifest_path,
        content_root=inputs.root,
        fonts=fonts,
        brand_asset=BRAND,
        output_directory=output or inputs.root / "output",
        overwrite=overwrite,
    )


def test_package_serialization_and_offline_immutable_inputs(
    inputs: SyntheticInputs, fonts: FontSet
) -> None:
    original = {p: p.read_bytes() for p in inputs.root.iterdir() if p.is_file()}
    output = inputs.root / "output"
    output.mkdir()
    (output / "video.mp4").write_bytes(b"existing renderer output")
    (output / "manifest.json").write_bytes(b"existing resolver output")
    with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
        metadata = package(inputs, fonts)
    assert metadata.review_status == "pending_human_review"
    assert metadata.working_title == inputs.recipe.publication.working_title
    assert metadata.thumbnail_hook == inputs.recipe.publication.thumbnail_hook
    assert len(metadata.attributions) == 15 and len(metadata.thumbnail_country_ids) == 3
    assert (
        metadata.snapshot_sha256 == hashlib.sha256(inputs.countries_path.read_bytes()).hexdigest()
    )
    assert (
        PublicationMetadata.model_validate_json((output / "metadata.json").read_text()) == metadata
    )
    assert (output / "title.txt").read_text() == metadata.working_title + "\n"
    assert (output / "description.txt").read_text() == metadata.description
    assert (
        metadata.thumbnail_sha256
        == hashlib.sha256((output / "thumbnail.png").read_bytes()).hexdigest()
    )
    assert (output / "video.mp4").read_bytes() == b"existing renderer output"
    assert (output / "manifest.json").read_bytes() == b"existing resolver output"
    assert all(path.read_bytes() == value for path, value in original.items())
    before = {name: (output / name).read_bytes() for name in OWNED_FILES}
    package(inputs, fonts, overwrite=True)
    assert all((output / name).read_bytes() == value for name, value in before.items())
    assert not list(inputs.root.glob(".publication-*"))
    assert not list(inputs.root.glob("*.lock"))


def test_required_attributions_and_notes_preserved(inputs: SyntheticInputs, fonts: FontSet) -> None:
    data = json.loads(inputs.countries_path.read_text())
    for country in data["countries"]:
        country["flag"].update(
            licence="CC-BY-SA-4.0",
            attribution="Exact Creator / CC-BY-SA-4.0",
            notes="Modified colour example; TEST ONLY",
        )
    inputs.countries_path.write_text(json.dumps(data))
    metadata = package(inputs, fonts)
    assert all(
        credit.attribution == "Exact Creator / CC-BY-SA-4.0" for credit in metadata.attributions
    )
    assert all(
        credit.notes == "Modified colour example; TEST ONLY" for credit in metadata.attributions
    )
    assert metadata.description.count("Exact Creator / CC-BY-SA-4.0") == 15
    assert all(credit.factual_sources for credit in metadata.attributions)


def test_draft_rejected_before_any_output(inputs: SyntheticInputs, fonts: FontSet) -> None:
    manifest = inputs.root / "manifest.json"
    manifest.write_text(resolve_files(inputs.countries_path, inputs.recipe_path).model_dump_json())
    data = json.loads(inputs.countries_path.read_text())
    data.update(editorial_status="draft", approved_by=None, approved_on=None)
    inputs.countries_path.write_text(json.dumps(data))
    with pytest.raises(PublicationError, match="approval"):
        package(inputs, fonts, manifest=manifest)
    assert not (inputs.root / "output").exists()


@pytest.mark.parametrize("change", ["manifest", "recipe", "snapshot", "asset"])
def test_stale_or_corrupt_inputs_rejected(
    inputs: SyntheticInputs, fonts: FontSet, change: str
) -> None:
    manifest = inputs.root / "manifest.json"
    value = resolve_files(inputs.countries_path, inputs.recipe_path).model_dump(mode="json")
    if change == "manifest":
        value["questions"][0]["prompt"] = "tampered prompt"
    manifest.write_text(json.dumps(value))
    if change == "recipe":
        data = json.loads(inputs.recipe_path.read_text())
        data["seed"] += 1
        inputs.recipe_path.write_text(json.dumps(data))
    elif change == "snapshot":
        data = json.loads(inputs.countries_path.read_text())
        data["countries"][0]["name"] += " edited"
        inputs.countries_path.write_text(json.dumps(data))
    elif change == "asset":
        (inputs.root / "test-only.png").write_bytes(b"corrupt")
    with pytest.raises(PublicationError, match="stale|modified|checksum"):
        package(inputs, fonts, manifest=manifest)
    assert not (inputs.root / "output").exists()


def test_overwrite_explicit_and_aliases_rejected(inputs: SyntheticInputs, fonts: FontSet) -> None:
    package(inputs, fonts)
    with pytest.raises(PublicationError, match="overwrite"):
        package(inputs, fonts)
    output = inputs.root / "output"
    (output / "title.txt").unlink()
    os.link(inputs.countries_path, output / "title.txt")
    with pytest.raises(PublicationError, match="alias"):
        package(inputs, fonts, overwrite=True)
    (output / "title.txt").unlink()
    (output / "title.txt").symlink_to(inputs.countries_path)
    with pytest.raises(PublicationError, match="alias"):
        package(inputs, fonts, overwrite=True)


@pytest.mark.parametrize("existing", [False, True])
def test_failed_commit_rolls_back_and_cleans(
    inputs: SyntheticInputs, fonts: FontSet, existing: bool
) -> None:
    output = inputs.root / "output"
    output.mkdir()
    if existing:
        for name in OWNED_FILES:
            (output / name).write_bytes(b"old:" + name.encode())
    original = {p.name: p.read_bytes() for p in output.iterdir()}
    operation = os.replace if existing else os.link
    calls = 0

    def fail_once(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected disk failure")
        operation(source, destination)

    with patch(
        "quiztalcoatl.publication.os.replace" if existing else "quiztalcoatl.publication.os.link",
        side_effect=fail_once,
    ):
        with pytest.raises(PublicationError, match="disk failure"):
            package(inputs, fonts, overwrite=existing)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == original
    assert not list(inputs.root.glob(".publication-*"))
    assert not list(inputs.root.glob("*.lock"))


def test_long_title_is_not_silently_truncated(inputs: SyntheticInputs, fonts: FontSet) -> None:
    data = json.loads(inputs.recipe_path.read_text())
    data["publication"]["working_title"] = "long " * 25
    inputs.recipe_path.write_text(json.dumps(data))
    with pytest.raises(PublicationError, match="100"):
        package(inputs, fonts)
    assert not (inputs.root / "output").exists()


def test_real_draft_still_rejected(fonts: FontSet, tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(PublicationError, match="editorial approval"):
        generate_package(
            root / "data/countries.json",
            root / "recipes/V-001.json",
            tmp_path / "nonexistent-manifest.json",
            content_root=root,
            brand_asset=BRAND,
            fonts=fonts,
            output_directory=tmp_path / "real",
        )
    assert not (tmp_path / "real").exists()


def test_source_changes_during_drawing_fail_closed(inputs: SyntheticInputs, fonts: FontSet) -> None:
    def change(
        questions: list[ResolvedQuestion],
        *,
        hook: str,
        question_count: int,
        content_root: Path,
        fonts: FontSet,
        brand_asset: Path,
    ) -> RenderedThumbnail:
        rendered = render_thumbnail(
            questions,
            hook=hook,
            question_count=question_count,
            content_root=content_root,
            fonts=fonts,
            brand_asset=brand_asset,
        )
        inputs.countries_path.write_text(inputs.countries_path.read_text() + " ")
        return rendered

    with patch("quiztalcoatl.publication.render_thumbnail", side_effect=change):
        with pytest.raises(PublicationError, match="changed"):
            package(inputs, fonts)
    assert not (inputs.root / "output").exists()


@pytest.mark.parametrize("kind", ["missing", "unverified", "licence"])
def test_incomplete_approval_or_assets_rejected(
    inputs: SyntheticInputs, fonts: FontSet, kind: str
) -> None:
    manifest = inputs.root / "manifest.json"
    manifest.write_text(resolve_files(inputs.countries_path, inputs.recipe_path).model_dump_json())
    data = json.loads(inputs.countries_path.read_text())
    if kind == "missing":
        (inputs.root / "test-only.png").unlink()
    elif kind == "unverified":
        data["countries"][0]["verification"]["flag"]["status"] = "needs_verification"
    else:
        data["countries"][0]["flag"]["licence"] = "unknown"
    inputs.countries_path.write_text(json.dumps(data))
    with pytest.raises(PublicationError, match="missing|verified|licence"):
        package(inputs, fonts, manifest=manifest)
    assert not (inputs.root / "output").exists()


def test_concurrent_package_lock_and_symlink_directory(
    inputs: SyntheticInputs, fonts: FontSet
) -> None:
    lock = inputs.root / ".output.publication.lock"
    lock.write_text("other operation")
    with pytest.raises(PublicationError, match="locked"):
        package(inputs, fonts)
    assert lock.read_text() == "other operation"
    lock.unlink()
    (inputs.root / "output").symlink_to(inputs.root, target_is_directory=True)
    with pytest.raises(PublicationError, match="symlink"):
        package(inputs, fonts)


@pytest.mark.parametrize("kind", ["unicode_bytes", "angle_brackets"])
def test_unuploadable_description_fails_without_dropping_credits(
    inputs: SyntheticInputs, fonts: FontSet, kind: str
) -> None:
    data = json.loads(inputs.countries_path.read_text())
    for country in data["countries"]:
        country["flag"]["attribution"] = "é" * 100 if kind == "unicode_bytes" else "Creator <name>"
    inputs.countries_path.write_text(json.dumps(data))
    with pytest.raises(PublicationError, match="5000 UTF-8 bytes"):
        package(inputs, fonts)
    assert not (inputs.root / "output").exists()


def test_long_provenance_notes_stay_complete_in_metadata(
    inputs: SyntheticInputs, fonts: FontSet
) -> None:
    data = json.loads(inputs.countries_path.read_text())
    notes = "Long internal provenance record. " * 100
    for country in data["countries"]:
        country["flag"]["notes"] = notes
    inputs.countries_path.write_text(json.dumps(data))
    metadata = package(inputs, fonts)
    assert all(credit.notes == notes for credit in metadata.attributions)
    assert len(metadata.description.encode()) <= 5000
