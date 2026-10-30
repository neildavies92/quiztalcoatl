"""Run the complete 355-second renderer using explicitly synthetic approved test inputs."""

import argparse
import hashlib
import json
import resource
import runpy
import sys
from pathlib import Path

from quiztalcoatl.resolver import resolve_files
from quiztalcoatl.video import render_video


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("output/m5-synthetic"))
    parser.add_argument("--font-dir", type=Path)
    parser.add_argument("--brand-asset", type=Path, required=True)
    parser.add_argument("--preset", choices=["ultrafast", "veryfast", "medium"], default="veryfast")
    args = parser.parse_args()
    # Reuse the existing clearly-labelled synthetic fixture producer; no real content is approved.
    fixture = runpy.run_path(str(Path(__file__).parent / "design/preview.py"))
    countries, recipe = fixture["prepare_synthetic_inputs"](args.output_root / "inputs")
    manifest_path = args.output_root / "manifest.synthetic.json"
    manifest_path.write_text(resolve_files(countries, recipe).model_dump_json(indent=2) + "\n")
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    self_before = resource.getrusage(resource.RUSAGE_SELF)
    report = render_video(
        countries,
        recipe,
        manifest_path,
        args.output_root / "video.synthetic.mp4",
        content_root=countries.parent,
        font_dir=args.font_dir,
        brand_asset=args.brand_asset,
        overwrite=True,
        preset=args.preset,
        preview_label="SYNTHETIC TECHNICAL PREVIEW • NOT FOR PUBLICATION",
    )
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    self_after = resource.getrusage(resource.RUSAGE_SELF)
    cpu = sum(
        (
            child_after.ru_utime - child_before.ru_utime,
            child_after.ru_stime - child_before.ru_stime,
            self_after.ru_utime - self_before.ru_utime,
            self_after.ru_stime - self_before.ru_stime,
        )
    )
    divisor = 1 if sys.platform == "darwin" else 1024
    metrics = {
        "status": "synthetic technical render; human pacing/visual/audio UAT pending",
        "video_file": "video.synthetic.mp4",
        "duration_seconds": 355,
        "decoded_frames": report.frames,
        "fps": 30,
        "audio": "none (silent video-only)",
        "preset": report.preset,
        "threads": 2,
        "wall_seconds": report.wall_seconds,
        "output_bytes": report.output_bytes,
        "temporary_peak_bytes": report.temporary_bytes,
        "cpu_seconds_including_children": cpu,
        "average_cpu_percent": cpu / report.wall_seconds * 100,
        "maximum_individual_ffmpeg_child_rss_bytes": child_after.ru_maxrss * divisor,
        "renderer_process_rss_bytes": self_after.ru_maxrss * divisor,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "warnings": [
            warning.replace(str(args.output_root.resolve()), "<OUTPUT_ROOT>")
            for warning in report.warnings
        ],
    }
    (args.output_root / "benchmark.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
