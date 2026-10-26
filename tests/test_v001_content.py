"""Integrity checks for real research drafts; these cannot grant editorial approval."""

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from PIL import Image

from quiztalcoatl.content import (
    ContentError,
    check_asset,
    load_recipe,
    load_snapshot,
    validate_inputs,
)
from quiztalcoatl.models import CountrySnapshot, QuizRecipe

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_IDS = (
    "france",
    "japan",
    "canada",
    "brazil",
    "germany",
    "italy",
    "spain",
    "portugal",
    "ireland",
    "sweden",
    "norway",
    "finland",
    "denmark",
    "poland",
    "greece",
    "india",
    "south-korea",
    "mexico",
    "argentina",
    "south-africa",
)


@pytest.fixture
def snapshot() -> CountrySnapshot:
    return load_snapshot(ROOT / "data/countries.json")


@pytest.fixture
def recipe() -> QuizRecipe:
    return load_recipe(ROOT / "recipes/V-001.json")


@pytest.fixture
def provenance() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ROOT / "docs/editorial/asset-provenance.json").read_text(encoding="utf-8")
    )
    return data


def test_real_inputs_are_structurally_valid(snapshot: CountrySnapshot, recipe: QuizRecipe) -> None:
    validate_inputs(snapshot, recipe, ROOT)
    assert snapshot.schema_version == recipe.schema_version == 1
    countries = {country.country_id: country for country in snapshot.countries}
    assert set(countries) == set(COUNTRY_IDS)
    assert len(recipe.candidate_country_ids) >= recipe.question_count == 15
    assert len(set(recipe.candidate_country_ids)) == len(recipe.candidate_country_ids)
    assert set(recipe.candidate_country_ids) <= countries.keys()
    assert len({country.name.casefold() for country in snapshot.countries}) == len(countries)
    for country_id in recipe.candidate_country_ids:
        country = countries[country_id]
        assert country.eligibility.flag_identification
        assert country.flag is not None
        assert country.flag_learning_fact is not None
        assert 1 <= len(country.flag_learning_fact.text.split()) <= 22
        assert country.flag_learning_fact.sources
        assert country.verification.identity.sources
        assert country.verification.flag is not None and country.verification.flag.sources
        assert country.verification.flag_learning_fact is not None
        assert country.verification.flag_learning_fact.sources
        assert country.continent and country.region and country.capitals


@pytest.mark.parametrize("country_id", COUNTRY_IDS)
def test_real_asset_integrity(
    country_id: str, snapshot: CountrySnapshot, provenance: dict[str, Any]
) -> None:
    country = next(country for country in snapshot.countries if country.country_id == country_id)
    asset = country.flag
    assert asset is not None
    record = next(item for item in provenance["assets"] if item["country_id"] == country_id)
    assert asset.path == record["path"] == f"assets/flags/{country_id}.png"
    assert record["source_file_title"] == f"File:Flag of {country.name}.svg"
    assert str(asset.source_url) == record["source_page_url"]
    assert "oldid=" in record["source_page_url"]
    assert record["original_file_timestamp"] and len(record["original_sha1"]) == 40
    assert record["source_licence_notices"]
    assert record["source_license_short_name"] == "Public domain"
    assert record["source_copyrighted"] == "False"
    # A recognised copyright designation does not establish legal usability of the flag.
    assert asset.licence == record["licence"] == "public-domain"
    assert asset.attribution
    check_asset(asset, ROOT, required=True, png=True)
    path = (ROOT / asset.path).resolve(strict=True)
    assert path.is_relative_to(ROOT) and path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset.sha256 == record["sha256"]
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.size == (record["width"], record["height"])
        assert image.width == 1920 and image.height >= 960
        assert image.height > 0 and image.width > 0
        # SVG imageinfo dimensions are integers; raster heights are independently rounded.
        assert (
            abs(image.width / image.height - record["original_width"] / record["original_height"])
            < 0.003
        )
        image.verify()
    for url in [str(asset.source_url), record["original_url"], record["derivative_url"]]:
        parsed = urlsplit(url)
        assert parsed.scheme == "https"
        assert parsed.hostname is not None and parsed.hostname.endswith("wikimedia.org")
    for review in (country.verification.identity, country.verification.flag_learning_fact):
        assert review is not None
        for source in review.sources:
            assert source.url.host is not None
            assert "example." not in source.url.host and ".invalid" not in source.url.host
            assert source.accessed_on is not None


def test_multi_capital_data_preserved(snapshot: CountrySnapshot) -> None:
    country = next(
        country for country in snapshot.countries if country.country_id == "south-africa"
    )
    assert [(city.name, city.role) for city in country.capitals] == [
        ("Pretoria", "administrative"),
        ("Cape Town", "legislative"),
        ("Bloemfontein", "judicial"),
    ]
    assert not country.eligibility.capital_questions
    assert country.eligibility.flag_identification
    assert country.capitals[2].notes is not None and "Johannesburg" in country.capitals[2].notes


def test_recipe_timing_and_scope(recipe: QuizRecipe) -> None:
    assert recipe.video_id == "V-001"
    assert recipe.topic == "Geography" and recipe.quiz_format == "flag_identification"
    assert recipe.difficulty == "Easy" and recipe.scope == "World"
    assert recipe.distractor_count == 3
    assert recipe.timing.question_seconds == 21
    assert recipe.timing.intro_seconds == 14
    assert recipe.timing.checkpoint_seconds == 4
    assert recipe.timing.checkpoint_after == [5, 10]
    assert recipe.timing.outro_seconds == 18
    assert recipe.timing.total_seconds(recipe.question_count) == 355


def test_publication_gate_uses_actual_review_state(
    snapshot: CountrySnapshot, recipe: QuizRecipe
) -> None:
    if snapshot.editorial_status == "approved":
        # Real reviewer metadata must be supplied through human UAT, never invented here.
        validate_inputs(snapshot, recipe, ROOT, publication_ready=True)
    else:
        assert snapshot.approved_by is None and snapshot.approved_on is None
        with pytest.raises(ContentError, match="requires explicit editorial approval"):
            validate_inputs(snapshot, recipe, ROOT, publication_ready=True)


def test_recorded_asset_concerns_cannot_enter_pool(
    snapshot: CountrySnapshot, recipe: QuizRecipe, provenance: dict[str, Any]
) -> None:
    countries = {country.country_id: country for country in snapshot.countries}
    for record in provenance["assets"]:
        if "EXCLUDED" in record["restrictions"]:
            assert not countries[record["country_id"]].eligibility.flag_identification
            assert record["country_id"] not in recipe.candidate_country_ids


def test_review_artifact_integrity(provenance: dict[str, Any]) -> None:
    preview = provenance["review_preview"]
    path = ROOT / preview["path"]
    assert path.resolve().is_relative_to(ROOT)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == preview["sha256"]
    assert preview["country_ids"] == list(COUNTRY_IDS)
    with Image.open(path) as image:
        assert image.format == "PNG" and image.size == (1600, 1500)
        image.verify()
    evidence = (ROOT / "docs/editorial/V-001-evidence.md").read_text(encoding="utf-8")
    review = (ROOT / "docs/editorial/V-001-review.md").read_text(encoding="utf-8")
    for country_id in COUNTRY_IDS:
        assert f"`{country_id}`" in evidence
        assert f"| `{country_id}` |" in review
