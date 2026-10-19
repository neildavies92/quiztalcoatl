"""Synthetic contract and filesystem cases; never editorial approval of real content."""

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PIL import Image
from pydantic import ValidationError
from typer.testing import CliRunner

from quiztalcoatl.cli import app
from quiztalcoatl.content import ContentError, load_recipe, load_snapshot, validate_inputs
from quiztalcoatl.models import CountrySnapshot, QuizRecipe, ResolvedQuizManifest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def draft() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / "countries.draft.json").read_text())
    return data


@pytest.fixture
def recipe_data() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / "V-001.test.json").read_text())
    return data


def snapshot(data: dict[str, Any]) -> CountrySnapshot:
    return CountrySnapshot.model_validate_json(json.dumps(data))


def recipe(data: dict[str, Any]) -> QuizRecipe:
    return QuizRecipe.model_validate_json(json.dumps(data))


@pytest.fixture
def approved(draft: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    asset = tmp_path / "test-only.png"
    Image.new("RGB", (2, 2), "red").save(asset)
    source = {"url": "https://example.invalid/test-only", "title": "Synthetic test provenance"}
    review = {
        "status": "verified",
        "sources": [source],
        "verified_by": "TEST-ONLY-REVIEWER",
        "verified_on": "2026-01-01",
    }
    draft.update(
        editorial_status="approved", approved_by="TEST-ONLY-REVIEWER", approved_on="2026-01-01"
    )
    for country in draft["countries"]:
        country["flag"] = {
            "path": asset.name,
            "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
            "source_url": source["url"],
            "licence": "public-domain",
        }
        country["flag_learning_fact"] = {"text": "Synthetic test explanation.", "sources": [source]}
        country["verification"] = {
            "identity": review.copy(),
            "flag": review.copy(),
            "flag_learning_fact": review.copy(),
        }
    return draft


def test_draft_and_recipe_round_trip(
    draft: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    countries, quiz = snapshot(draft), recipe(recipe_data)
    validate_inputs(countries, quiz, tmp_path)
    assert CountrySnapshot.model_validate_json(countries.model_dump_json()) == countries
    assert QuizRecipe.model_validate_json(quiz.model_dump_json()) == quiz
    assert countries.editorial_status == "draft"
    assert countries.countries[0].verification.identity.status == "needs_verification"


def test_approved_round_trip(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    countries = snapshot(approved)
    with patch("socket.socket", side_effect=AssertionError("network forbidden")):
        validate_inputs(countries, recipe(recipe_data), tmp_path, publication_ready=True)
    assert CountrySnapshot.model_validate_json(countries.model_dump_json()) == countries
    assert countries.countries[0].outline is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", "1"),
        ("extra", 1),
        ("snapshot_id", "bad ID"),
        ("snapshot_id", ""),
    ],
)
def test_invalid_snapshot_fields(draft: dict[str, Any], field: str, value: object) -> None:
    draft[field] = value
    with pytest.raises(ValidationError):
        snapshot(draft)


def test_missing_required(draft: dict[str, Any]) -> None:
    del draft["countries"][0]["eligibility"]
    with pytest.raises(ValidationError, match="eligibility"):
        snapshot(draft)


@pytest.mark.parametrize(
    "field,value", [("country_id", "test-country-01"), ("name", "  TEST   Country 01 ")]
)
def test_duplicate_country(draft: dict[str, Any], field: str, value: str) -> None:
    draft["countries"][1][field] = value
    with pytest.raises(ValidationError, match="unique"):
        snapshot(draft)


@pytest.mark.parametrize("url", ["", "not-a-url", "ftp://example.invalid/a", "file:///tmp/a"])
def test_source_urls(approved: dict[str, Any], url: str) -> None:
    approved["countries"][0]["flag_learning_fact"]["sources"][0]["url"] = url
    with pytest.raises(ValidationError):
        snapshot(approved)


@pytest.mark.parametrize("field", ["sources", "verified_by", "verified_on"])
def test_incomplete_verification(approved: dict[str, Any], field: str) -> None:
    del approved["countries"][0]["verification"]["identity"][field]
    with pytest.raises(ValidationError):
        snapshot(approved)


@pytest.mark.parametrize("field", ["approved_by", "approved_on"])
def test_incomplete_approval(approved: dict[str, Any], field: str) -> None:
    del approved[field]
    with pytest.raises(ValidationError, match="approved"):
        snapshot(approved)


@pytest.mark.parametrize(
    "path", ["../escape.png", "/tmp/a.png", "C:/a.png", "a/../../b", "..\\a.png", "."]
)
def test_unsafe_paths(approved: dict[str, Any], path: str) -> None:
    approved["countries"][0]["flag"]["path"] = path
    with pytest.raises(ValidationError, match="path"):
        snapshot(approved)


@pytest.mark.parametrize(
    "failure", ["missing", "reference", "checksum", "directory", "symlink", "not-png", "fake-png"]
)
def test_bad_assets(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path, failure: str
) -> None:
    flag = approved["countries"][0]["flag"]
    if failure == "missing":
        flag["path"] = "missing.png"
    elif failure == "reference":
        approved["countries"][0]["flag"] = None
    elif failure == "checksum":
        flag["sha256"] = "0" * 64
    elif failure == "directory":
        (tmp_path / "directory.png").mkdir()
        flag["path"] = "directory.png"
    elif failure == "symlink":
        (tmp_path / "escape.png").symlink_to(tmp_path.parent / "outside.png")
        flag["path"] = "escape.png"
    else:
        path = tmp_path / ("image.jpg" if failure == "not-png" else "fake.png")
        Image.new("RGB", (2, 2)).save(path, format="JPEG")
        flag.update(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ContentError, match="test-country-01"):
        validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path, publication_ready=True)


@pytest.mark.parametrize("category", ["identity", "flag", "flag_learning_fact"])
def test_unverified_publication(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path, category: str
) -> None:
    approved["countries"][0]["verification"][category]["status"] = "needs_verification"
    countries = snapshot(approved)
    validate_inputs(countries, recipe(recipe_data), tmp_path)
    with pytest.raises(ContentError, match="verified"):
        validate_inputs(countries, recipe(recipe_data), tmp_path, publication_ready=True)


@pytest.mark.parametrize("licence", ["unknown", "Unlicensed", "TBD", "not-a-reviewed-licence"])
def test_unknown_licence(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path, licence: str
) -> None:
    approved["countries"][0]["flag"]["licence"] = licence
    with pytest.raises(ContentError, match="licence"):
        validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path, publication_ready=True)


def test_attribution_required(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    approved["countries"][0]["flag"]["licence"] = "CC-BY-4.0"
    with pytest.raises(ContentError, match="attribution"):
        validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path, publication_ready=True)


def test_unapproved(draft: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path) -> None:
    with pytest.raises(ContentError, match="editorial approval"):
        validate_inputs(snapshot(draft), recipe(recipe_data), tmp_path, publication_ready=True)


def test_unknown_candidate(
    draft: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    recipe_data["candidate_country_ids"][0] = "unknown-country"
    with pytest.raises(ContentError, match="unknown-country"):
        validate_inputs(snapshot(draft), recipe(recipe_data), tmp_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("question_count", 0),
        ("question_count", 14),
        ("question_count", "15"),
        ("question_count", True),
        ("distractor_count", 2),
        ("seed", "42"),
        ("quiz_format", "capital_questions"),
        ("schema_version", 2),
        ("candidate_country_ids", ["test-country-01"]),
        ("candidate_country_ids", ["test-country-01"] * 15),
    ],
)
def test_bad_recipe(recipe_data: dict[str, Any], field: str, value: object) -> None:
    recipe_data[field] = value
    with pytest.raises(ValidationError):
        recipe(recipe_data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("intro_seconds", -1),
        ("outro_seconds", "5"),
        ("question_seconds", 20),
        ("checkpoint_after", [5, 5]),
        ("checkpoint_after", [10, 5]),
        ("checkpoint_after", [15]),
        ("checkpoint_after", [0]),
    ],
)
def test_bad_timing(recipe_data: dict[str, Any], field: str, value: object) -> None:
    recipe_data["timing"][field] = value
    with pytest.raises(ValidationError):
        recipe(recipe_data)


def test_multi_capital_flag_only(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    country = approved["countries"][0]
    country["capitals"] = [
        {"name": "Test Administrative City", "role": "administrative"},
        {"name": "Test Legislative City", "role": "legislative"},
        {"name": "Test Judicial City", "role": "judicial"},
    ]
    countries = snapshot(approved)
    validate_inputs(countries, recipe(recipe_data), tmp_path, publication_ready=True)
    assert len(countries.countries[0].capitals) == 3
    country["eligibility"]["capital_questions"] = True
    with pytest.raises(ValidationError, match="exactly one capital"):
        snapshot(approved)


@pytest.mark.parametrize("contents", ["{", '{"schema_version":1,"schema_version":2}', '{"x":NaN}'])
def test_malformed_json(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(contents)
    with pytest.raises(ContentError, match="Malformed JSON"):
        load_snapshot(path)


def test_missing_and_non_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    with pytest.raises(ContentError, match="Cannot read"):
        load_snapshot(path)
    path.write_bytes(b"\xff")
    with pytest.raises(ContentError, match="UTF-8"):
        load_snapshot(path)


def test_schema_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{}")
    with pytest.raises(ContentError, match="Schema violation"):
        load_recipe(path)


def test_cli_draft_and_publication_failure() -> None:
    args = [
        "validate",
        "--countries",
        str(FIXTURES / "countries.draft.json"),
        "--recipe",
        str(FIXTURES / "V-001.test.json"),
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "not approval" in result.output
    failure = CliRunner().invoke(app, [*args, "--publication-ready"])
    assert failure.exit_code == 1
    assert "editorial approval" in failure.output


def test_cli_approved_independent_of_cwd(
    approved: dict[str, Any],
    recipe_data: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    countries_path = tmp_path / "countries.json"
    recipe_path = tmp_path / "recipe.json"
    countries_path.write_text(json.dumps(approved))
    recipe_path.write_text(json.dumps(recipe_data))
    before = countries_path.read_bytes()
    monkeypatch.chdir(tmp_path.parent)
    args = [
        "validate",
        "--countries",
        str(countries_path),
        "--recipe",
        str(recipe_path),
        "--publication-ready",
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "publication readiness" in result.output
    assert countries_path.read_bytes() == before
    countries_path.write_text("{")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "Malformed JSON" in result.output


@pytest.fixture
def manifest_data(approved: dict[str, Any], recipe_data: dict[str, Any]) -> dict[str, Any]:
    options = [
        {"country_id": country["country_id"], "label": country["name"]}
        for country in approved["countries"][:4]
    ]
    country = approved["countries"][0]
    return {
        "schema_version": 1,
        "video_id": "V-002",
        "questions": [
            {
                "ordinal": 1,
                "question_id": "test-question-01",
                "prompt": "TEST ONLY: Which synthetic country?",
                "correct_answer": options[0].copy(),
                "options": options,
                "correct_answer_index": 0,
                "asset": country["flag"],
                "explanation": country["flag_learning_fact"],
                "sources": country["flag_learning_fact"]["sources"],
            }
        ],
        "recipe_sha256": "a" * 64,
        "snapshot_sha256": "b" * 64,
        "seed": 42,
        "theme_id": "test-only-theme",
        "timing": {**recipe_data["timing"], "checkpoint_after": []},
        "expected_total_seconds": 31,
    }


def test_manifest_round_trip(manifest_data: dict[str, Any]) -> None:
    manifest = ResolvedQuizManifest.model_validate_json(json.dumps(manifest_data))
    assert ResolvedQuizManifest.model_validate_json(manifest.model_dump_json()) == manifest
    assert manifest.questions[0].correct_answer == manifest.questions[0].options[0]


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate-id",
        "duplicate-label",
        "answer-index",
        "answer-label",
        "option-count",
        "ordinal",
        "duration",
        "schema",
        "extra",
    ],
)
def test_invalid_manifest(manifest_data: dict[str, Any], failure: str) -> None:
    question = manifest_data["questions"][0]
    if failure == "duplicate-id":
        question["options"][1]["country_id"] = question["options"][0]["country_id"]
    elif failure == "duplicate-label":
        question["options"][1]["label"] = question["options"][0]["label"].upper()
    elif failure == "answer-index":
        question["correct_answer_index"] = 1
    elif failure == "answer-label":
        question["correct_answer"]["label"] = "Different label"
    elif failure == "option-count":
        question["options"].pop()
    elif failure == "ordinal":
        question["ordinal"] = 2
    elif failure == "duration":
        manifest_data["expected_total_seconds"] = 1
    elif failure == "schema":
        manifest_data["schema_version"] = 2
    else:
        question["unexpected"] = True
    with pytest.raises(ValidationError):
        ResolvedQuizManifest.model_validate_json(json.dumps(manifest_data))


@pytest.mark.parametrize("failure", ["ineligible", "missing-fact", "missing-review"])
def test_incomplete_flag_input(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path, failure: str
) -> None:
    country = approved["countries"][0]
    if failure == "ineligible":
        country["eligibility"]["flag_identification"] = False
    elif failure == "missing-fact":
        country["flag_learning_fact"] = None
    else:
        country["verification"]["flag"] = None
    with pytest.raises(ContentError, match="test-country-01"):
        validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path, publication_ready=True)


def test_missing_draft_asset_is_allowed(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    approved["editorial_status"] = "draft"
    (tmp_path / "test-only.png").unlink()
    validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path)


def test_empty_licence_rejected(approved: dict[str, Any]) -> None:
    approved["countries"][0]["flag"]["licence"] = "   "
    with pytest.raises(ValidationError, match="licence"):
        snapshot(approved)


def test_corrupt_png_with_matching_checksum(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    asset = tmp_path / "corrupt.png"
    asset.write_bytes(b"\x89PNG\r\n\x1a\ninvalid chunks")
    approved["countries"][0]["flag"].update(
        path=asset.name, sha256=hashlib.sha256(asset.read_bytes()).hexdigest()
    )
    with pytest.raises(ContentError, match="test-country-01"):
        validate_inputs(snapshot(approved), recipe(recipe_data), tmp_path, publication_ready=True)


def test_explicit_content_root(
    approved: dict[str, Any], recipe_data: dict[str, Any], tmp_path: Path
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    countries_path, recipe_path = data_dir / "countries.json", data_dir / "recipe.json"
    countries_path.write_text(json.dumps(approved))
    recipe_path.write_text(json.dumps(recipe_data))
    result = CliRunner().invoke(
        app,
        [
            "validate",
            "--countries",
            str(countries_path),
            "--recipe",
            str(recipe_path),
            "--content-root",
            str(tmp_path),
            "--publication-ready",
        ],
    )
    assert result.exit_code == 0, result.output


def test_distractor_pool_minimum(recipe_data: dict[str, Any]) -> None:
    recipe_data.update(
        video_id="V-002",
        question_count=1,
        candidate_country_ids=recipe_data["candidate_country_ids"][:3],
    )
    recipe_data["timing"]["checkpoint_after"] = []
    with pytest.raises(ValidationError, match="insufficient candidate pool"):
        recipe(recipe_data)
