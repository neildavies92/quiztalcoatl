"""Generate test-only publication previews without approving real country content."""

import argparse
import hashlib
import json
from pathlib import Path

from design.preview import prepare_synthetic_inputs
from PIL import Image, ImageDraw

from quiztalcoatl.graphics import load_fonts
from quiztalcoatl.publication import generate_package
from quiztalcoatl.resolver import resolve_files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("output/publication-synthetic"))
    parser.add_argument("--font-dir", type=Path)
    parser.add_argument(
        "--brand-asset", type=Path, default=Path("assets/brand/quiztalcoatl-logo.png")
    )
    args = parser.parse_args()
    countries, recipe = prepare_synthetic_inputs(args.output_root / "inputs")
    snapshot = json.loads(countries.read_text())
    for index, country in enumerate(snapshot["countries"]):
        flag = Image.new("RGB", (900, 600), "#12615A")
        draw = ImageDraw.Draw(flag)
        colours = ["#FF976A", "#FFD45B", "#F7FFF7"]
        shapes = [
            [(0, 0), (420, 300), (0, 600)],
            [(0, 0), (450, 220), (900, 0), (900, 150), (450, 400), (0, 150)],
            [(0, 170), (900, 170), (900, 420), (0, 420)],
            [(0, 0), (900, 600), (550, 600), (0, 240)],
            [(0, 600), (900, 0), (900, 260), (350, 600)],
        ]
        draw.polygon(shapes[index % 5], fill=colours[index % 3])
        draw.rectangle((540, 0, 620, 600), fill=colours[(index + 1) % 3])
        draw.ellipse((690, 200 + index * 4, 850, 360 + index * 4), fill=colours[(index + 2) % 3])
        path = countries.parent / f"synthetic-{index:02}.png"
        flag.save(path)
        country["flag"]["path"] = path.name
        country["flag"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    countries.write_text(json.dumps(snapshot, indent=2) + "\n")
    data = json.loads(recipe.read_text())
    data["publication"] = {
        "working_title": "SYNTHETIC PREVIEW — Guess 15 Countries From Their Flags",
        "thumbnail_hook": "NAME THESE FLAGS",
    }
    recipe.write_text(json.dumps(data, indent=2) + "\n")
    manifest_path = args.output_root / "manifest.synthetic.json"
    manifest_path.write_text(resolve_files(countries, recipe).model_dump_json(indent=2) + "\n")
    package = args.output_root / "V-001"
    generate_package(
        countries,
        recipe,
        manifest_path,
        content_root=countries.parent,
        brand_asset=args.brand_asset,
        fonts=load_fonts(args.font_dir),
        output_directory=package,
        overwrite=True,
    )
    with Image.open(package / "thumbnail.png") as image:
        image.resize((320, 180), Image.Resampling.LANCZOS).save(
            args.output_root / "thumbnail-mobile.png"
        )
    print(f"Synthetic preview only; human UAT pending: {package}")


if __name__ == "__main__":
    main()
