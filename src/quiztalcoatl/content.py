"""Offline JSON loading, local asset checks and explicit publication gates."""

import hashlib
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from quiztalcoatl.models import (
    AssetReference,
    Contract,
    CountrySnapshot,
    QuizRecipe,
    VerificationRecord,
)


class ContentError(ValueError):
    """Actionable content validation failure suitable for CLI output."""


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"invalid JSON numeric constant: {value}")


def load_contract[T: Contract](path: Path, model: type[T]) -> T:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContentError(f"Cannot read UTF-8 JSON {path}: {exc}") from exc
    try:
        json.loads(raw, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
    except ValueError as exc:
        raise ContentError(f"Malformed JSON in {path}: {exc}") from exc
    try:
        # JSON mode accepts ISO dates while strict validation rejects coercible field values.
        return model.model_validate_json(raw)
    except ValidationError as exc:
        raise ContentError(f"Schema violation in {path}:\n{exc}") from exc


def load_snapshot(path: Path) -> CountrySnapshot:
    return load_contract(path, CountrySnapshot)


def load_recipe(path: Path) -> QuizRecipe:
    return load_contract(path, QuizRecipe)


def check_asset(asset: AssetReference, root: Path, *, required: bool, png: bool) -> None:
    try:
        resolved_root = root.resolve(strict=True)
        path = (resolved_root / asset.path).resolve()
        if not resolved_root.is_dir() or not path.is_relative_to(resolved_root):
            raise ContentError(
                f"asset path escapes content root or root is not a directory: {asset.path}"
            )
        if not path.exists():
            if required:
                raise ContentError(f"missing asset: {asset.path}")
            return
        if not path.is_file():
            raise ContentError(f"asset must be a regular file: {asset.path}")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != asset.sha256:
            raise ContentError(
                f"asset checksum mismatch: {asset.path}; expected {asset.sha256}, got {actual}"
            )
        if png:
            if path.suffix.lower() != ".png":
                raise ContentError(f"production flag must use PNG: {asset.path}")
            with Image.open(path) as image:
                if image.format != "PNG":
                    raise ContentError(f"production flag is not PNG data: {asset.path}")
                image.verify()
    except (
        OSError,
        RuntimeError,
        ValueError,
        SyntaxError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as exc:
        if isinstance(exc, ContentError):
            raise
        raise ContentError(f"Cannot validate asset {asset.path}: {exc}") from exc


def _require_verified(record: VerificationRecord | None, label: str) -> None:
    if record is None or record.status != "verified":
        raise ContentError(
            f"publication readiness: {label} requires explicit verified review metadata"
        )


def _require_licence(asset: AssetReference) -> None:
    # This is a metadata policy, not a legal assessment of the image or its provenance.
    if asset.licence not in {"public-domain", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"}:
        raise ContentError(
            f"publication readiness: asset {asset.path} has unknown/unsupported licence "
            f"{asset.licence!r}; use a documented licence designation after editorial review"
        )
    if asset.licence in {"CC-BY-4.0", "CC-BY-SA-4.0"} and not asset.attribution:
        raise ContentError(f"publication readiness: asset {asset.path} requires attribution")


def validate_inputs(
    snapshot: CountrySnapshot,
    recipe: QuizRecipe,
    content_root: Path,
    *,
    publication_ready: bool = False,
) -> None:
    countries = {country.country_id: country for country in snapshot.countries}
    unknown = set(recipe.candidate_country_ids) - countries.keys()
    if unknown:
        raise ContentError(f"recipe references unknown country IDs: {', '.join(sorted(unknown))}")
    for country in snapshot.countries:
        for category in ("flag", "outline"):
            asset = country.flag if category == "flag" else country.outline
            if asset is not None:
                try:
                    check_asset(asset, content_root, required=False, png=False)
                except ContentError as exc:
                    raise ContentError(f"{country.country_id}.{category}: {exc}") from exc
    if not publication_ready:
        return
    if snapshot.editorial_status != "approved":
        raise ContentError("publication readiness: snapshot requires explicit editorial approval")
    for country_id in recipe.candidate_country_ids:
        country = countries[country_id]
        try:
            if not country.eligibility.flag_identification:
                raise ContentError(
                    "publication readiness: flag_identification eligibility is false"
                )
            _require_verified(country.verification.identity, "identity")
            _require_verified(country.verification.flag, "flag asset")
            _require_verified(country.verification.flag_learning_fact, "flag learning fact")
            if country.flag_learning_fact is None:
                raise ContentError("publication readiness: missing flag_learning_fact")
            if country.flag is None:
                raise ContentError("publication readiness: missing flag asset reference")
            _require_licence(country.flag)
            check_asset(country.flag, content_root, required=True, png=True)
        except ContentError as exc:
            raise ContentError(f"{country_id}: {exc}") from exc
