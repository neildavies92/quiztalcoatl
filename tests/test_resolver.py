"""Synthetic approved fixtures only; no real editorial approvals or production output."""

import hashlib
import json
import random
import socket
from pathlib import Path
from typing import Literal, NamedTuple
from unittest.mock import patch

import pytest
from PIL import Image
from pydantic import ValidationError

from quiztalcoatl.content import ContentError, load_recipe, load_snapshot
from quiztalcoatl.models import CountrySnapshot, QuizRecipe, ResolvedQuizManifest
from quiztalcoatl.resolver import rank_country_ids, resolve_files, resolve_quiz


class SyntheticInputs(NamedTuple):
    snapshot: CountrySnapshot
    recipe: QuizRecipe
    countries_path: Path
    recipe_path: Path
    root: Path


@pytest.fixture
def inputs(tmp_path: Path) -> SyntheticInputs:
    """Twenty explicitly test-only countries and one tiny generated PNG, not real content."""
    image_path = tmp_path / "test-only.png"
    Image.new("RGB", (3, 2), "red").save(image_path)
    source = {"url": "https://example.invalid/synthetic-source", "title": "TEST ONLY"}
    review = {
        "status": "verified",
        "sources": [source],
        "verified_by": "TEST-ONLY-REVIEWER",
        "verified_on": "2026-01-01",
    }
    country_ids = [f"test-country-{number:02}" for number in range(1, 21)]
    data = {
        "schema_version": 1,
        "snapshot_id": "test-only-approved",
        "editorial_status": "approved",
        "approved_by": "TEST-ONLY-REVIEWER",
        "approved_on": "2026-01-01",
        "countries": [
            {
                "country_id": country_id,
                "name": f"Test Country {number:02}",
                "continent": "TEST ONLY",
                "region": "TEST ONLY",
                "capitals": [],
                "flag": {
                    "path": image_path.name,
                    "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
                    "source_url": source["url"],
                    "licence": "public-domain",
                },
                "flag_learning_fact": {
                    "text": f"TEST ONLY: Synthetic fact {number:02}.",
                    "sources": [source],
                },
                "eligibility": {
                    "flag_identification": True,
                    "capital_questions": False,
                    "outline_identification": False,
                },
                "verification": {"identity": review, "flag": review, "flag_learning_fact": review},
            }
            for number, country_id in enumerate(country_ids, 1)
        ],
    }
    quiz = {
        "schema_version": 1,
        "video_id": "V-001",
        "topic": "Geography",
        "quiz_format": "flag_identification",
        "difficulty": "Easy",
        "scope": "World",
        "question_count": 15,
        "candidate_country_ids": country_ids,
        "seed": 20261026,
        "distractor_count": 3,
        "timing": {
            "question_seconds": 21,
            "intro_seconds": 14,
            "checkpoint_seconds": 4,
            "checkpoint_after": [5, 10],
            "outro_seconds": 18,
        },
        "theme_id": "test-only-theme",
        "publication": {"working_title": "TEST ONLY", "thumbnail_hook": "TEST ONLY"},
    }
    countries_path, recipe_path = tmp_path / "countries.json", tmp_path / "recipe.json"
    countries_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    recipe_path.write_text(json.dumps(quiz, indent=2) + "\n", encoding="utf-8")
    return SyntheticInputs(
        load_snapshot(countries_path),
        load_recipe(recipe_path),
        countries_path,
        recipe_path,
        tmp_path,
    )


def pure(inputs: SyntheticInputs, recipe: QuizRecipe | None = None) -> ResolvedQuizManifest:
    return resolve_quiz(
        inputs.snapshot,
        recipe if recipe is not None else inputs.recipe,
        snapshot_sha256="a" * 64,
        recipe_sha256="b" * 64,
    )


def test_question_and_answer_integrity(inputs: SyntheticInputs) -> None:
    manifest = pure(inputs)
    assert len(manifest.questions) == 15
    correct_ids = [question.correct_answer.country_id for question in manifest.questions]
    assert len(set(correct_ids)) == 15
    pool = set(inputs.recipe.candidate_country_ids)
    for question in manifest.questions:
        option_ids = [option.country_id for option in question.options]
        assert len(option_ids) == len(set(option_ids)) == 4
        assert len({option.label for option in question.options}) == 4
        assert set(option_ids) <= pool
        assert option_ids.count(question.correct_answer.country_id) == 1
        assert question.options[question.correct_answer_index] == question.correct_answer
        distractors = [option for option in question.options if option != question.correct_answer]
        assert len(distractors) == 3
    assert len({question.correct_answer_index for question in manifest.questions}) >= 3


def test_repeated_resolution_and_json_are_identical(inputs: SyntheticInputs) -> None:
    first, second = pure(inputs), pure(inputs)
    assert first == second
    assert first.model_dump_json() == second.model_dump_json()
    assert ResolvedQuizManifest.model_validate_json(first.model_dump_json()) == first


def test_reordered_records_and_candidates(inputs: SyntheticInputs) -> None:
    snapshot = inputs.snapshot.model_copy(
        update={"countries": list(reversed(inputs.snapshot.countries))}
    )
    recipe = inputs.recipe.model_copy(
        update={"candidate_country_ids": list(reversed(inputs.recipe.candidate_country_ids))}
    )
    result = resolve_quiz(snapshot, recipe, snapshot_sha256="a" * 64, recipe_sha256="b" * 64)
    assert result == pure(inputs)


def test_different_seeds(inputs: SyntheticInputs) -> None:
    recipe = inputs.recipe.model_copy(update={"seed": -19})
    alternative = pure(inputs, recipe)
    assert alternative == pure(inputs, recipe)
    assert alternative.questions != pure(inputs).questions
    assert alternative.seed == -19


def test_no_global_random_or_network_or_filesystem(
    inputs: SyntheticInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("pure resolution must not access randomness, files or network")

    monkeypatch.setattr(random, "random", forbidden)
    monkeypatch.setattr(random, "sample", forbidden)
    monkeypatch.setattr(random, "shuffle", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    assert len(pure(inputs).questions) == 15


def test_sources_facts_and_assets_preserved(inputs: SyntheticInputs) -> None:
    by_id = {country.country_id: country for country in inputs.snapshot.countries}
    for question in pure(inputs).questions:
        country = by_id[question.correct_answer.country_id]
        assert question.explanation == country.flag_learning_fact
        assert country.flag_learning_fact is not None
        assert question.sources == country.flag_learning_fact.sources
        assert question.asset == country.flag
        assert question.question_id == f"v-001-flag-{country.country_id}"
        assert question.prompt == "Which country does this flag represent?"


def test_output_does_not_alias_inputs(inputs: SyntheticInputs) -> None:
    before = inputs.snapshot.model_dump_json(), inputs.recipe.model_dump_json()
    result = pure(inputs)
    result.questions[0].asset.notes = "TEST mutation"
    result.questions[0].explanation.text = "TEST mutation"
    result.questions[0].sources[0].title = "TEST mutation"
    result.timing.intro_seconds = 100
    assert before == (inputs.snapshot.model_dump_json(), inputs.recipe.model_dump_json())


def test_duration_and_portability(inputs: SyntheticInputs) -> None:
    result = pure(inputs)
    assert result.expected_total_seconds == 355
    assert result.theme_id == "test-only-theme"
    text = result.model_dump_json()
    assert str(inputs.root) not in text
    assert "generated_at" not in text
    assert "timestamp" not in text


@pytest.mark.parametrize(
    "failure",
    [
        "unapproved",
        "ineligible",
        "identity",
        "flag-review",
        "fact-review",
        "flag",
        "fact",
        "licence",
        "attribution",
    ],
)
def test_pure_rejects_bad_metadata(inputs: SyntheticInputs, failure: str) -> None:
    data = json.loads(inputs.snapshot.model_dump_json())
    country = data["countries"][0]
    if failure == "unapproved":
        data["editorial_status"] = "draft"
    elif failure == "ineligible":
        country["eligibility"]["flag_identification"] = False
    elif failure in {"identity", "flag-review", "fact-review"}:
        key = {"identity": "identity", "flag-review": "flag", "fact-review": "flag_learning_fact"}[
            failure
        ]
        country["verification"][key]["status"] = "needs_verification"
    elif failure in {"flag", "fact"}:
        country["flag" if failure == "flag" else "flag_learning_fact"] = None
    elif failure == "licence":
        country["flag"]["licence"] = "unknown"
    else:
        country["flag"]["licence"] = "CC-BY-4.0"
    snapshot = CountrySnapshot.model_validate_json(json.dumps(data))
    with pytest.raises(ContentError, match="approved|test-country-01"):
        resolve_quiz(snapshot, inputs.recipe, snapshot_sha256="a" * 64, recipe_sha256="b" * 64)


@pytest.mark.parametrize("failure", ["unknown", "insufficient"])
def test_actionable_pool_errors(inputs: SyntheticInputs, failure: str) -> None:
    ids = inputs.recipe.candidate_country_ids.copy()
    if failure == "unknown":
        ids[0] = "unknown-country"
    else:
        ids = ids[:3]
    # Deliberately bypass normal construction to exercise the resolver's defensive pool guard.
    recipe = inputs.recipe.model_copy(update={"candidate_country_ids": ids})
    with pytest.raises(ContentError, match="unknown country ID|insufficient eligible candidates"):
        pure(inputs, recipe)


@pytest.mark.parametrize("field", ["snapshot_sha256", "recipe_sha256"])
def test_invalid_input_hashes(inputs: SyntheticInputs, field: str) -> None:
    hashes = {"snapshot_sha256": "a" * 64, "recipe_sha256": "b" * 64}
    hashes[field] = "not-a-checksum"
    with pytest.raises(ValidationError, match=field):
        resolve_quiz(inputs.snapshot, inputs.recipe, **hashes)


def test_original_file_hashes_and_no_mutation(inputs: SyntheticInputs) -> None:
    snapshot_bytes = inputs.countries_path.read_bytes()
    recipe_bytes = inputs.recipe_path.read_bytes()
    result = resolve_files(inputs.countries_path, inputs.recipe_path)
    assert result.snapshot_sha256 == hashlib.sha256(snapshot_bytes).hexdigest()
    assert result.recipe_sha256 == hashlib.sha256(recipe_bytes).hexdigest()
    assert inputs.countries_path.read_bytes() == snapshot_bytes
    assert inputs.recipe_path.read_bytes() == recipe_bytes
    assert result == resolve_files(inputs.countries_path, inputs.recipe_path)


def test_reformatted_input_hash_changes_without_reselection(inputs: SyntheticInputs) -> None:
    first = resolve_files(inputs.countries_path, inputs.recipe_path)
    inputs.countries_path.write_text(inputs.snapshot.model_dump_json() + "\n\n", encoding="utf-8")
    inputs.recipe_path.write_text(inputs.recipe.model_dump_json() + "\n\n", encoding="utf-8")
    second = resolve_files(inputs.countries_path, inputs.recipe_path)
    assert first.snapshot_sha256 != second.snapshot_sha256
    assert first.recipe_sha256 != second.recipe_sha256
    assert first.questions == second.questions


def test_file_validation_is_offline(inputs: SyntheticInputs) -> None:
    with patch("socket.socket", side_effect=AssertionError("network forbidden")):
        assert len(resolve_files(inputs.countries_path, inputs.recipe_path).questions) == 15


@pytest.mark.parametrize(
    "failure", ["unapproved", "unverified", "missing", "checksum", "malformed", "unknown"]
)
def test_file_validation_rejects_invalid_inputs(inputs: SyntheticInputs, failure: str) -> None:
    if failure == "missing":
        (inputs.root / "test-only.png").unlink()
    elif failure == "checksum":
        (inputs.root / "test-only.png").write_bytes(b"corrupt asset")
    elif failure == "malformed":
        inputs.countries_path.write_text("{")
    else:
        data = json.loads(inputs.countries_path.read_text())
        if failure == "unapproved":
            data["editorial_status"] = "draft"
        elif failure == "unverified":
            data["countries"][0]["verification"]["identity"]["status"] = "needs_verification"
        else:
            data["countries"].pop(0)
        inputs.countries_path.write_text(json.dumps(data))
    with pytest.raises(
        ContentError,
        match="approval|verified|missing asset|checksum|Malformed JSON|unknown country",
    ):
        resolve_files(inputs.countries_path, inputs.recipe_path)


def test_explicit_root_and_other_working_directory(
    inputs: SyntheticInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = inputs.root / "data"
    data_dir.mkdir()
    countries_path = data_dir / "countries.json"
    countries_path.write_bytes(inputs.countries_path.read_bytes())
    monkeypatch.chdir(inputs.root.parent)
    result = resolve_files(countries_path, inputs.recipe_path, content_root=inputs.root)
    assert len(result.questions) == 15


def test_missing_input_file(inputs: SyntheticInputs) -> None:
    with pytest.raises(ContentError, match="Cannot read resolution input"):
        resolve_files(inputs.root / "missing.json", inputs.recipe_path)


@pytest.mark.parametrize("change", ["rewrite", "remove"])
def test_input_changes_during_validation_are_rejected(inputs: SyntheticInputs, change: str) -> None:
    def changing_loader(path: Path) -> QuizRecipe:
        loaded = load_recipe(path)
        if change == "rewrite":
            path.write_bytes(path.read_bytes() + b"\n")
        else:
            path.unlink()
        return loaded

    with patch("quiztalcoatl.resolver.load_recipe", side_effect=changing_loader):
        with pytest.raises(ContentError, match="changed during validation|Cannot recheck"):
            resolve_files(inputs.countries_path, inputs.recipe_path)


def test_synthetic_manual_inspection(inputs: SyntheticInputs) -> None:
    """Run with -s to display a synthetic question and its real temporary input hashes."""
    result = resolve_files(inputs.countries_path, inputs.recipe_path)
    print("\nTEST ONLY — synthetic resolver UAT; not the real V-001 output")
    print(
        json.dumps(
            {
                "seed": result.seed,
                "snapshot_sha256": result.snapshot_sha256,
                "recipe_sha256": result.recipe_sha256,
                "question": result.questions[0].model_dump(mode="json"),
            },
            indent=2,
        )
    )
    assert result.questions[0].correct_answer in result.questions[0].options


@pytest.mark.parametrize(
    "domain,expected",
    [
        ("questions", ["gamma", "alpha", "delta", "beta"]),
        ("distractors", ["gamma", "beta", "delta", "alpha"]),
        ("options", ["beta", "delta", "gamma", "alpha"]),
    ],
)
def test_fixed_ranking_vectors(
    domain: Literal["questions", "distractors", "options"], expected: list[str]
) -> None:
    assert (
        rank_country_ids(
            ["alpha", "beta", "gamma", "delta"],
            seed=42,
            domain=domain,
            question_country_id="alpha",
        )
        == expected
    )


def test_fixed_selection_and_option_vectors(inputs: SyntheticInputs) -> None:
    result = pure(inputs)
    expected = [16, 20, 4, 7, 14, 9, 12, 3, 10, 18, 17, 13, 15, 11, 6]
    assert [question.correct_answer.country_id for question in result.questions] == [
        f"test-country-{number:02}" for number in expected
    ]
    assert [option.country_id for option in result.questions[0].options] == [
        "test-country-15",
        "test-country-10",
        "test-country-16",
        "test-country-05",
    ]
    assert [question.correct_answer_index for question in result.questions] == [
        2,
        2,
        1,
        2,
        0,
        0,
        1,
        3,
        0,
        3,
        1,
        3,
        1,
        3,
        0,
    ]
