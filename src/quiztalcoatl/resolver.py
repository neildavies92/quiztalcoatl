"""Deterministic flag-question resolution, independent of rendering and live data."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from quiztalcoatl.content import (
    ContentError,
    _require_licence,
    _require_verified,
    load_recipe,
    load_snapshot,
    validate_inputs,
)
from quiztalcoatl.models import (
    AnswerOption,
    CountryRecord,
    CountrySnapshot,
    QuizRecipe,
    ResolvedQuestion,
    ResolvedQuizManifest,
)


def rank_country_ids(
    country_ids: list[str],
    *,
    seed: int,
    domain: Literal["questions", "distractors", "options"],
    question_country_id: str = "",
) -> list[str]:
    """Rank IDs by the documented v1 domain-separated SHA-256 ordering."""

    def key(country_id: str) -> tuple[bytes, str]:
        payload = json.dumps(
            [
                "quiztalcoatl-resolver-v1",
                "flag_identification",
                domain,
                seed,
                question_country_id,
                country_id,
            ],
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
        return hashlib.sha256(payload).digest(), country_id

    return sorted(country_ids, key=key)


def _eligible_candidates(snapshot: CountrySnapshot, recipe: QuizRecipe) -> dict[str, CountryRecord]:
    """Check publication metadata without I/O; disk integrity belongs to resolve_files."""
    if snapshot.editorial_status != "approved" or not (
        snapshot.approved_by and snapshot.approved_on
    ):
        raise ContentError(
            "resolution requires an explicitly approved snapshot with reviewer and date"
        )
    countries = {country.country_id: country for country in snapshot.countries}
    candidates: dict[str, CountryRecord] = {}
    for country_id in sorted(recipe.candidate_country_ids):
        country = countries.get(country_id)
        if country is None:
            raise ContentError(f"resolution candidate {country_id}: unknown country ID")
        try:
            if not country.eligibility.flag_identification:
                raise ContentError("flag_identification eligibility is false")
            _require_verified(country.verification.identity, "identity")
            _require_verified(country.verification.flag, "flag asset")
            _require_verified(country.verification.flag_learning_fact, "flag learning fact")
            if country.flag is None or country.flag_learning_fact is None:
                raise ContentError("missing flag asset reference or flag learning explanation")
            _require_licence(country.flag)
        except ContentError as exc:
            raise ContentError(f"resolution candidate {country_id}: {exc}") from exc
        candidates[country_id] = country
    if len(candidates) < max(recipe.question_count, recipe.distractor_count + 1):
        raise ContentError(
            "resolution has insufficient eligible candidates for questions and distractors"
        )
    return candidates


def resolve_quiz(
    snapshot: CountrySnapshot,
    recipe: QuizRecipe,
    *,
    snapshot_sha256: str,
    recipe_sha256: str,
) -> ResolvedQuizManifest:
    """Resolve validated models purely; callers must validate local files before rendering.

    This function checks publication metadata but deliberately cannot check asset bytes.
    Use resolve_files for production input loading and complete publication validation.
    """
    candidates = _eligible_candidates(snapshot, recipe)
    selected = rank_country_ids(list(candidates), seed=recipe.seed, domain="questions")
    questions: list[ResolvedQuestion] = []
    for ordinal, country_id in enumerate(selected[: recipe.question_count], start=1):
        country = candidates[country_id]
        distractors = rank_country_ids(
            [candidate for candidate in candidates if candidate != country_id],
            seed=recipe.seed,
            domain="distractors",
            question_country_id=country_id,
        )[: recipe.distractor_count]
        ordered = rank_country_ids(
            [country_id, *distractors],
            seed=recipe.seed,
            domain="options",
            question_country_id=country_id,
        )
        options = [
            AnswerOption(country_id=option_id, label=candidates[option_id].name)
            for option_id in ordered
        ]
        # Publication metadata checks above establish these required optional fields.
        assert country.flag is not None
        assert country.flag_learning_fact is not None
        questions.append(
            ResolvedQuestion(
                ordinal=ordinal,
                question_id=f"{recipe.video_id.lower()}-flag-{country_id}",
                prompt="Which country does this flag represent?",
                correct_answer=AnswerOption(country_id=country_id, label=country.name),
                options=options,
                correct_answer_index=ordered.index(country_id),
                asset=country.flag.model_copy(deep=True),
                explanation=country.flag_learning_fact.model_copy(deep=True),
                sources=[
                    source.model_copy(deep=True) for source in country.flag_learning_fact.sources
                ],
            )
        )
    return ResolvedQuizManifest(
        schema_version=1,
        video_id=recipe.video_id,
        questions=questions,
        recipe_sha256=recipe_sha256,
        snapshot_sha256=snapshot_sha256,
        seed=recipe.seed,
        theme_id=recipe.theme_id,
        timing=recipe.timing.model_copy(deep=True),
        expected_total_seconds=recipe.timing.total_seconds(recipe.question_count),
    )


def resolve_files(
    countries_path: Path,
    recipe_path: Path,
    *,
    content_root: Path | None = None,
) -> ResolvedQuizManifest:
    """Load original JSON bytes, require complete publication readiness, then resolve.

    No files are written. A source changing during loading/validation is rejected so its
    recorded checksum cannot silently identify bytes different from the loaded input.
    """
    try:
        snapshot_bytes = countries_path.read_bytes()
        recipe_bytes = recipe_path.read_bytes()
    except OSError as exc:
        raise ContentError(f"Cannot read resolution input: {exc}") from exc
    snapshot = load_snapshot(countries_path)
    recipe = load_recipe(recipe_path)
    validate_inputs(
        snapshot,
        recipe,
        content_root if content_root is not None else countries_path.resolve().parent,
        publication_ready=True,
    )
    try:
        if (
            countries_path.read_bytes() != snapshot_bytes
            or recipe_path.read_bytes() != recipe_bytes
        ):
            raise ContentError(
                "resolution input changed during validation; retry with stable files"
            )
    except OSError as exc:
        raise ContentError(f"Cannot recheck resolution input: {exc}") from exc
    return resolve_quiz(
        snapshot,
        recipe,
        snapshot_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
        recipe_sha256=hashlib.sha256(recipe_bytes).hexdigest(),
    )
