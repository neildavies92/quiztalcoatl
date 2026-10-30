"""Reproducible static design previews from explicitly synthetic approved test inputs."""

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageDraw

from quiztalcoatl.graphics import CardLayout, load_fonts, render_card, save_png
from quiztalcoatl.resolver import resolve_files


def prepare_synthetic_inputs(root: Path) -> tuple[Path, Path]:
    """Create test-only review metadata and geometric artwork, never real country data."""
    root.mkdir(parents=True, exist_ok=True)
    flag = Image.new("RGB", (1200, 800), "#12615A")
    draw = ImageDraw.Draw(flag)
    draw.polygon([(0, 0), (500, 400), (0, 800)], fill="#F1C86C")
    draw.rectangle((700, 0, 840, 800), fill="#F4F1E8")
    draw.ellipse((890, 280, 1130, 520), fill="#D46C4C")
    flag_path = root / "synthetic-flag.png"
    flag.save(flag_path)
    source = {
        "url": "https://example.invalid/test-only-design",
        "title": "Synthetic visual fixture",
    }
    review = {
        "status": "verified",
        "sources": [source],
        "verified_by": "TEST-ONLY-REVIEWER",
        "verified_on": "2026-01-01",
    }
    labels = ["Northhaven", "Sundale", "Verdant Isles", "Meridian"] * 5
    countries = []
    for number in range(1, 21):
        label = (
            labels[number - 1] if number in (5, 10, 15, 16) else f"Synthetic Country {number:02}"
        )
        countries.append(
            {
                "country_id": f"test-country-{number:02}",
                "name": label,
                "continent": "TEST ONLY",
                "region": "TEST ONLY",
                "capitals": [],
                "flag": {
                    "path": flag_path.name,
                    "sha256": hashlib.sha256(flag_path.read_bytes()).hexdigest(),
                    "source_url": source["url"],
                    "licence": "public-domain",
                    "notes": "Generated synthetic geometry; not a national flag.",
                },
                "flag_learning_fact": {
                    "text": (
                        "In this fictional flag, the gold triangle stands for curiosity "
                        "and the coral sun for discovery."
                    ),
                    "sources": [source],
                },
                "eligibility": {
                    "flag_identification": True,
                    "capital_questions": False,
                    "outline_identification": False,
                },
                "verification": {"identity": review, "flag": review, "flag_learning_fact": review},
            }
        )
    snapshot = {
        "schema_version": 1,
        "snapshot_id": "test-only-design",
        "editorial_status": "approved",
        "approved_by": "TEST-ONLY-REVIEWER",
        "approved_on": "2026-01-01",
        "countries": countries,
    }
    recipe = {
        "schema_version": 1,
        "video_id": "V-001",
        "topic": "Geography",
        "quiz_format": "flag_identification",
        "difficulty": "Easy",
        "scope": "World",
        "question_count": 15,
        "candidate_country_ids": [country["country_id"] for country in countries],
        "seed": 20261026,
        "distractor_count": 3,
        "theme_id": "geography-pilot",
        "timing": {
            "question_seconds": 21,
            "intro_seconds": 14,
            "checkpoint_seconds": 4,
            "checkpoint_after": [5, 10],
            "outro_seconds": 18,
        },
        "publication": {"working_title": "TEST ONLY DESIGN PREVIEW", "thumbnail_hook": "TEST ONLY"},
    }
    snapshot_path, recipe_path = root / "countries.synthetic.json", root / "recipe.synthetic.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    return snapshot_path, recipe_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, help="Explicit DejaVu regular/Bold directory.")
    parser.add_argument("--output-root", type=Path, default=Path("output/design-v2"))
    parser.add_argument(
        "--brand-asset",
        type=Path,
        required=True,
        help="Explicit supplied transparent mascot/logo PNG.",
    )
    args = parser.parse_args()
    fonts = load_fonts(args.font_dir)
    countries, recipe = prepare_synthetic_inputs(args.output_root / "inputs")
    question = resolve_files(countries, recipe).questions[0]
    question.ordinal = 7
    layout = CardLayout(
        total_questions=15, preview_label="SYNTHETIC DESIGN PREVIEW • HUMAN VISUAL UAT PENDING"
    )
    for name, reveal in (("question.png", False), ("reveal.png", True)):
        card = render_card(
            question,
            layout,
            content_root=countries.parent,
            fonts=fonts,
            reveal=reveal,
            brand_asset=args.brand_asset,
        )
        print(save_png(card, args.output_root, name, overwrite=True))
        mobile = card.image.resize((480, 270), Image.Resampling.LANCZOS)
        save_png(
            replace(card, image=mobile),
            args.output_root,
            name.replace(".png", "-mobile.png"),
            overwrite=True,
        )
    stress = question.model_copy(deep=True)
    for option, label in zip(
        stress.options,
        [
            "Federated Republic of the Northern Archipelago",
            "United Islands of Southern Meridian",
            "Autonomous Highland Federation",
            "Commonwealth of the Verdant Coast",
        ],
        strict=True,
    ):
        option.label = label
    stress.correct_answer = stress.options[stress.correct_answer_index].model_copy(deep=True)
    stress.explanation.text = (
        "This fictional archipelago uses a gold triangle for curiosity, "
        "an ivory band for shared knowledge, "
        "and a coral sun for discovery across its many islands."
    )
    card = render_card(
        stress,
        layout,
        content_root=countries.parent,
        fonts=fonts,
        reveal=True,
        brand_asset=args.brand_asset,
    )
    print(save_png(card, args.output_root, "stress.png", overwrite=True))
    save_png(
        replace(card, image=card.image.resize((480, 270), Image.Resampling.LANCZOS)),
        args.output_root,
        "stress-mobile.png",
        overwrite=True,
    )


if __name__ == "__main__":
    main()
