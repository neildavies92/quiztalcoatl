"""Offline, publication-gated, deterministic review artifacts; never upload anything."""

import hashlib
import os
import tempfile
from pathlib import Path

from quiztalcoatl.content import ContentError, load_contract, load_recipe, load_snapshot
from quiztalcoatl.graphics import FontSet, GraphicsError
from quiztalcoatl.models import Contract, ResolvedQuizManifest
from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.thumbnail import encode_thumbnail, render_thumbnail

OWNED_FILES = ("thumbnail.png", "title.txt", "description.txt", "metadata.json")


class PublicationError(ValueError):
    """Inputs or safe publication artifact generation could not be satisfied."""


class Attribution(Contract):
    country_id: str
    asset_path: str
    asset_sha256: str
    source_url: str
    licence: str
    attribution: str | None
    notes: str | None
    factual_sources: list[dict[str, str | None]]


class PublicationMetadata(Contract):
    schema_version: int = 1
    video_id: str
    working_title: str
    description: str
    suggested_tags: list[str]
    thumbnail_hook: str
    review_status: str = "pending_human_review"
    review_note: str = (
        "Editorial validation passed; thumbnail, copy, rights and final video UAT pending."
    )
    snapshot_sha256: str
    recipe_sha256: str
    manifest_sha256: str
    brand_sha256: str
    thumbnail_sha256: str
    thumbnail_country_ids: list[str]
    attributions: list[Attribution]


def _metadata(
    manifest: ResolvedQuizManifest,
    title: str,
    hook: str,
    manifest_bytes: bytes,
    brand: bytes,
    thumbnail: bytes,
) -> PublicationMetadata:
    if (
        len(title) > 100
        or any(ord(character) < 32 for character in title)
        or any(character in title for character in "<>")
    ):
        raise PublicationError(
            "working title must be a single line of at most 100 characters without < or >"
        )
    attributions = [
        Attribution(
            country_id=question.correct_answer.country_id,
            asset_path=question.asset.path,
            asset_sha256=question.asset.sha256,
            source_url=str(question.asset.source_url),
            licence=question.asset.licence,
            attribution=question.asset.attribution,
            notes=question.asset.notes,
            factual_sources=[source.model_dump(mode="json") for source in question.sources],
        )
        for question in manifest.questions
    ]
    lines = [
        title,
        "",
        "Welcome to QUIZtalcoatl!",
        f"Name the countries behind {len(manifest.questions)} flags. Choose from four answers, "
        "keep your score, and discover a short flag fact with every reveal.",
        "",
        f"How many did you get out of {len(manifest.questions)}? Share your score in the comments "
        "and tell us which flag surprised you.",
        "",
        "Flag artwork and learning sources:",
    ]
    for question, credit in zip(manifest.questions, attributions, strict=True):
        lines.append(f"{question.correct_answer.label}: {credit.source_url} [{credit.licence}]")
        if credit.attribution:
            lines.append(credit.attribution)
        for source in question.sources:
            lines.append(f"Fact: {source.title or 'Source'} — {source.url}")
    description = "\n".join(lines) + "\n"
    if len(description.encode("utf-8")) > 5000 or "<" in description or ">" in description:
        raise PublicationError(
            "description exceeds 5000 UTF-8 bytes or contains < or >; review attribution/copy"
        )
    return PublicationMetadata(
        video_id=manifest.video_id,
        working_title=title,
        description=description,
        suggested_tags=["flag quiz", "geography quiz", "country flags", "QUIZtalcoatl"],
        thumbnail_hook=hook,
        snapshot_sha256=manifest.snapshot_sha256,
        recipe_sha256=manifest.recipe_sha256,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        brand_sha256=hashlib.sha256(brand).hexdigest(),
        thumbnail_sha256=hashlib.sha256(thumbnail).hexdigest(),
        thumbnail_country_ids=[q.correct_answer.country_id for q in manifest.questions[:3]],
        attributions=attributions,
    )


def _same_file(first: Path, second: Path) -> bool:
    return first.resolve() == second.resolve() or (
        first.exists() and second.exists() and first.samefile(second)
    )


def generate_package(
    countries_path: Path,
    recipe_path: Path,
    manifest_path: Path,
    *,
    content_root: Path,
    brand_asset: Path,
    fonts: FontSet,
    output_directory: Path,
    overwrite: bool = False,
) -> PublicationMetadata:
    """Stage all four files, validate sources afresh, then commit with failure rollback.

    Each file appears atomically; four-file replacement is not a filesystem transaction.
    A sibling exclusive lock prevents concurrent calls through this API. Unrelated output
    files (video/manifest) are preserved. Consumers must wait for this function to return.
    """
    try:
        fresh = resolve_files(countries_path, recipe_path, content_root=content_root)
        manifest_bytes = manifest_path.read_bytes()
        supplied = load_contract(manifest_path, ResolvedQuizManifest)
        if manifest_path.read_bytes() != manifest_bytes:
            raise PublicationError("manifest changed during loading")
        if supplied != fresh:
            raise PublicationError(
                "manifest is stale or modified; resolve the approved sources again"
            )
        snapshot, recipe = load_snapshot(countries_path), load_recipe(recipe_path)
        protected = [countries_path, recipe_path, manifest_path, brand_asset]
        protected.extend(
            content_root / asset.path
            for country in snapshot.countries
            for asset in (country.flag, country.outline)
            if asset is not None
        )
        protected_bytes = {path: path.read_bytes() for path in protected if path.is_file()}
        if protected_bytes[manifest_path] != manifest_bytes:
            raise PublicationError("manifest changed during loading")
        brand_bytes = brand_asset.read_bytes()
        protected_bytes[brand_asset] = brand_bytes
        directory = output_directory.absolute()
        if directory.is_symlink():
            raise PublicationError("output directory must not be a symlink")
        destinations = [directory / name for name in OWNED_FILES]
        for destination in destinations:
            if destination.is_symlink() or any(
                _same_file(destination, source) for source in protected
            ):
                raise PublicationError("output must not replace or alias any source input")
            if destination.exists() and (not overwrite or not destination.is_file()):
                raise PublicationError("publication output exists; explicitly request overwrite")
        thumbnail = render_thumbnail(
            fresh.questions,
            hook=recipe.publication.thumbnail_hook,
            question_count=recipe.question_count,
            content_root=content_root,
            fonts=fonts,
            brand_asset=brand_asset,
        )
        thumbnail_bytes = encode_thumbnail(thumbnail)
        metadata = _metadata(
            fresh,
            recipe.publication.working_title,
            recipe.publication.thumbnail_hook,
            manifest_bytes,
            brand_bytes,
            thumbnail_bytes,
        )
        payloads = (
            thumbnail_bytes,
            (metadata.working_title + "\n").encode(),
            metadata.description.encode(),
            (metadata.model_dump_json(indent=2) + "\n").encode(),
        )
        # Confirm that recipe fields and every source are still the bytes we resolved.
        if (
            hashlib.sha256(countries_path.read_bytes()).hexdigest() != fresh.snapshot_sha256
            or hashlib.sha256(recipe_path.read_bytes()).hexdigest() != fresh.recipe_sha256
            or resolve_files(countries_path, recipe_path, content_root=content_root) != fresh
            or any(path.read_bytes() != value for path, value in protected_bytes.items())
        ):
            raise PublicationError("source changed while generating publication artifacts")
        directory.parent.mkdir(parents=True, exist_ok=True)
        lock = directory.parent / f".{directory.name}.publication.lock"
        try:
            lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise PublicationError("publication output is locked by another operation") from exc
        os.close(lock_fd)
        try:
            _publish(directory, payloads, overwrite=overwrite)
        finally:
            lock.unlink()
        return metadata
    except (OSError, ContentError, GraphicsError) as exc:
        raise PublicationError(str(exc)) from exc


def _publish(directory: Path, payloads: tuple[bytes, ...], *, overwrite: bool) -> None:
    with tempfile.TemporaryDirectory(prefix=".publication-", dir=directory.parent) as temporary:
        stage = Path(temporary)
        for name, payload in zip(OWNED_FILES, payloads, strict=True):
            with (stage / name).open("wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        directory.mkdir(exist_ok=True)
        old: dict[str, bytes | None] = {}
        committed: list[str] = []
        try:
            for name in OWNED_FILES:
                destination = directory / name
                if destination.is_symlink():
                    raise PublicationError("publication output became a symlink")
                if destination.exists() and not overwrite:
                    raise PublicationError(
                        "publication output exists; explicitly request overwrite"
                    )
                old[name] = destination.read_bytes() if destination.exists() else None
                if overwrite:
                    os.replace(stage / name, destination)
                else:
                    os.link(stage / name, destination)
                committed.append(name)
        except (OSError, PublicationError):
            for name in reversed(committed):
                prior = old[name]
                destination = directory / name
                if prior is None:
                    destination.unlink()
                else:
                    (stage / name).write_bytes(prior)
                    os.replace(stage / name, destination)
            raise
