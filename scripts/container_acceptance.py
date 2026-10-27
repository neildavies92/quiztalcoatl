"""Exercise the real runtime image offline, including host-mounted media output."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str], *, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, timeout=120)
    if result.returncode != expected:
        raise RuntimeError(
            f"Command exited {result.returncode}, expected {expected}: {command}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def input_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in ("data", "recipes", "assets")
        for path in sorted((root / directory).rglob("*"))
        if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="quiztalcoatl:local")
    parser.add_argument("--output", type=Path, default=Path("output/container-smoke"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if os.getuid() == 0:
        raise RuntimeError("Run this host acceptance script as a non-root developer/CI user.")
    before = input_hashes(root)
    sandbox = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=64m",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
    ]
    mapped = [*sandbox, "--user", f"{os.getuid()}:{os.getgid()}"]
    mounts: list[str] = []
    for directory in ("data", "recipes", "assets"):
        mounts += ["--mount", f"type=bind,src={root / directory},dst=/work/{directory},readonly"]
    mounts += ["--mount", f"type=bind,src={output},dst=/work/output"]
    mounts += [
        "--mount",
        f"type=bind,src={root / 'tests/fixtures'},dst=/work/test-fixtures,readonly",
    ]

    for option in ("--help", "--version", "doctor"):
        result = run([*sandbox, args.image, option])
        assert result.stdout.strip(), f"empty {option} output"
        if option == "doctor":
            assert "ffmpeg version" in result.stdout and "ffprobe version" in result.stdout
        print(f"Offline runtime {option}: passed")

    inspection = """
import importlib.util, os, shutil
from pathlib import Path
from PIL import Image, ImageFont
assert os.getuid() != 0
assert Path.cwd() == Path('/work')
for name in ('uv', 'ruff', 'mypy', 'pytest', 'make', 'pip'):
    assert shutil.which(name) is None, name
for name in ('pytest', 'mypy', 'ruff', 'pip'):
    assert importlib.util.find_spec(name) is None, name
for path in ('/app', '/build', '/work/data', '/work/recipes', '/work/assets'):
    assert not Path(path).exists(), path
for root in (Path('/opt'), Path('/work')):
    for path in root.rglob('*'):
        forbidden = {'.git', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
        assert path.name not in forbidden and not path.name.startswith('.env'), path
font_dir = Path(os.environ['QUIZTALCOATL_FONT_DIR'])
for name in ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf'):
    assert (font_dir / name).is_file(), name
    font = ImageFont.truetype(str(font_dir / name), 32)
    assert font.getbbox('QUIZtalcoatl')[2] > 0
assert Image.new('RGB', (2, 2)).size == (2, 2)
assert shutil.which('ffmpeg') and shutil.which('ffprobe')
print('Non-root runtime, installed fonts/Pillow, clean image and absent dev tooling: passed')
"""
    print(run([*sandbox, "--entrypoint", "python", args.image, "-c", inspection]).stdout.strip())

    readonly = """
from pathlib import Path
try:
    Path('/work/data/container-should-not-write.txt').write_text('must fail')
except OSError as exc:
    assert exc.errno == 30, exc
else:
    raise AssertionError('input mount was writable')
Path('/work/output/host-permission-check.txt').write_text('host readable and deletable')
"""
    run([*mapped, *mounts, "--entrypoint", "python", args.image, "-c", readonly])
    permission_file = output / "host-permission-check.txt"
    assert permission_file.read_text() == "host readable and deletable"
    assert permission_file.stat().st_uid == os.getuid()
    permission_file.unlink()
    assert not permission_file.exists()
    print("Read-only inputs and host-user read/delete/ownership: passed")

    run(
        [
            *mapped,
            *mounts,
            args.image,
            "validate",
            "--countries",
            "data/countries.json",
            "--recipe",
            "recipes/V-001.json",
            "--content-root",
            "/work",
        ]
    )
    rejection = run(
        [
            *mapped,
            *mounts,
            args.image,
            "resolve",
            "--countries",
            "test-fixtures/countries.draft.json",
            "--recipe",
            "test-fixtures/V-001.test.json",
            "--content-root",
            "/work",
            "--output",
            "/work/output/rejected/manifest.json",
        ],
        expected=1,
    )
    assert "editorial approval" in rejection.stderr + rejection.stdout
    assert not (output / "rejected").exists()
    print("Real content validates; synthetic draft rejection creates no output: passed")

    generator = """
import hashlib, json
from pathlib import Path
from PIL import Image
root = Path('/work/synthetic')
Image.new('RGB', (4, 3), '#123456').save(root / 'flag.png')
source = {'url': 'https://example.invalid/test-only', 'title': 'SYNTHETIC TEST ONLY'}
review = {'status': 'verified', 'sources': [source],
          'verified_by': 'TEST-ONLY-REVIEWER', 'verified_on': '2000-01-01'}
snapshot = json.loads(Path('/work/test-fixtures/countries.draft.json').read_text())
snapshot.update(editorial_status='approved', approved_by='TEST-ONLY-REVIEWER',
                approved_on='2000-01-01')
flag_sha256 = hashlib.sha256((root / 'flag.png').read_bytes()).hexdigest()
for country in snapshot['countries']:
    country['flag'] = {'path': 'flag.png', 'sha256': flag_sha256,
                       'source_url': source['url'], 'licence': 'public-domain'}
    country['flag_learning_fact'] = {'text': 'Synthetic test explanation.', 'sources': [source]}
    country['verification'] = {'identity': review, 'flag': review, 'flag_learning_fact': review}
recipe = json.loads(Path('/work/test-fixtures/V-001.test.json').read_text())
recipe['timing'].update(intro_seconds=14, checkpoint_seconds=4, outro_seconds=18)
(root / 'countries.json').write_text(json.dumps(snapshot), encoding='utf-8')
(root / 'recipe.json').write_text(json.dumps(recipe), encoding='utf-8')
"""
    with (
        tempfile.TemporaryDirectory(prefix="quiztalcoatl-inputs-", dir="/tmp") as directory,
        tempfile.TemporaryDirectory(prefix="synthetic-container-", dir=output) as results_directory,
    ):
        synthetic = Path(directory)
        synthetic_outputs = Path(results_directory)
        writable = ["--mount", f"type=bind,src={synthetic},dst=/work/synthetic"]
        run([*mapped, *mounts, *writable, "--entrypoint", "python", args.image, "-c", generator])
        original = {path.name: path.read_bytes() for path in synthetic.iterdir()}
        readonly_mounts = ["--mount", f"type=bind,src={synthetic},dst=/work/synthetic,readonly"]
        base = [
            *mapped,
            *mounts,
            *readonly_mounts,
            args.image,
            "resolve",
            "--countries",
            "/work/synthetic/countries.json",
            "--recipe",
            "/work/synthetic/recipe.json",
            "--content-root",
            "/work/synthetic",
            "--output",
        ]
        # Outputs use the existing host bind mount; input material stays read-only.
        first = synthetic_outputs / "synthetic-first.json"
        second = synthetic_outputs / "synthetic-second.json"
        first_target = f"/work/output/{synthetic_outputs.name}/synthetic-first.json"
        second_target = f"/work/output/{synthetic_outputs.name}/synthetic-second.json"
        try:
            run([*base, first_target])
            run([*base, second_target])
            first_bytes = first.read_bytes()
            assert first_bytes == second.read_bytes()
            manifest = json.loads(first_bytes)
            assert len(manifest["questions"]) == 15
            assert manifest["expected_total_seconds"] == 355
            assert (
                manifest["snapshot_sha256"]
                == hashlib.sha256(original["countries.json"]).hexdigest()
            )
            assert manifest["recipe_sha256"] == hashlib.sha256(original["recipe.json"]).hexdigest()
            for question in manifest["questions"]:
                assert len({option["country_id"] for option in question["options"]}) == 4
                assert (
                    question["options"][question["correct_answer_index"]]
                    == question["correct_answer"]
                )
            refusal = run([*base, first_target], expected=1)
            assert "overwrite" in refusal.stdout + refusal.stderr
            assert first.read_bytes() == first_bytes
            run([*base, first_target, "--overwrite"])
            assert first.read_bytes() == first_bytes
            assert first.stat().st_uid == os.getuid()
            assert {name: (synthetic / name).read_bytes() for name in original} == original
        finally:
            first.unlink(missing_ok=True)
            second.unlink(missing_ok=True)
    print(
        "Synthetic approved resolution on host mount, atomic output/repeat/overwrite/hashes: passed"
    )

    run(
        [
            *mapped,
            *mounts,
            "--entrypoint",
            "ffmpeg",
            args.image,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x180:rate=30",
            "-t",
            "2",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "/work/output/smoke.mp4",
        ]
    )
    probe = run(
        [
            *mapped,
            *mounts,
            "--entrypoint",
            "ffprobe",
            args.image,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            "/work/output/smoke.mp4",
        ]
    )
    metadata = json.loads(probe.stdout)
    videos = [stream for stream in metadata["streams"] if stream["codec_type"] == "video"]
    assert len(videos) == 1
    video = videos[0]
    assert video["codec_name"] == "h264"
    assert (video["width"], video["height"]) == (320, 180)
    assert video["pix_fmt"] == "yuv420p" and video["r_frame_rate"] == "30/1"
    assert 1.8 <= float(metadata["format"]["duration"]) <= 2.2
    media = output / "smoke.mp4"
    assert media.stat().st_size > 0 and media.stat().st_uid == os.getuid()
    with media.open("rb") as stream:
        assert stream.read(16)
    assert input_hashes(root) == before
    print(f"Real offline libx264/ffprobe H.264 smoke and unchanged inputs: passed ({media})")
    print("Human UAT remaining: open the MP4 in a host player and assess playback.")


if __name__ == "__main__":
    main()
