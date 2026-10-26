"""Production CLI integration uses synthetic approvals, never real editorial sign-off."""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from test_resolver import SyntheticInputs
from test_resolver import inputs as inputs
from typer.testing import CliRunner

from quiztalcoatl.cli import app
from quiztalcoatl.content import load_snapshot
from quiztalcoatl.models import ResolvedQuizManifest


def arguments(inputs: SyntheticInputs, output: Path, *, overwrite: bool = False) -> list[str]:
    args = [
        "resolve",
        "--countries",
        str(inputs.countries_path),
        "--recipe",
        str(inputs.recipe_path),
        "--content-root",
        str(inputs.root),
        "--output",
        str(output),
    ]
    return [*args, "--overwrite"] if overwrite else args


@pytest.mark.parametrize("force_color", [None, "1"])
def test_help_and_required_output(inputs: SyntheticInputs, force_color: str | None) -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0 and "resolve" in result.output
    result = CliRunner().invoke(app, ["resolve", "--help"], env={"FORCE_COLOR": force_color})
    assert result.exit_code == 0
    help_text = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert "--output" in help_text and "--overwrite" in help_text
    args = arguments(inputs, inputs.root / "unused.json")
    result = CliRunner().invoke(app, args[:-2], env={"FORCE_COLOR": force_color})
    error_text = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert result.exit_code != 0 and "--output" in error_text


def test_manifest_integrity_repeatability_and_input_preservation(inputs: SyntheticInputs) -> None:
    source_paths = [inputs.countries_path, inputs.recipe_path, inputs.root / "test-only.png"]
    before = {path: path.read_bytes() for path in source_paths}
    first, second = inputs.root / "output/first.json", inputs.root / "output/second.json"
    with patch("socket.socket", side_effect=AssertionError("network forbidden")):
        for output in (first, second):
            result = CliRunner().invoke(app, arguments(inputs, output))
            assert result.exit_code == 0, result.output
            assert "15 questions, 355 seconds" in result.output
    raw = first.read_bytes()
    assert raw == second.read_bytes() and raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b'\n  "schema_version": 1,' in raw
    manifest = ResolvedQuizManifest.model_validate_json(raw)
    assert manifest.video_id == "V-001" and manifest.expected_total_seconds == 355
    assert manifest.snapshot_sha256 == hashlib.sha256(before[inputs.countries_path]).hexdigest()
    assert manifest.recipe_sha256 == hashlib.sha256(before[inputs.recipe_path]).hexdigest()
    expected = [16, 20, 4, 7, 14, 9, 12, 3, 10, 18, 17, 13, 15, 11, 6]
    assert [q.correct_answer.country_id for q in manifest.questions] == [
        f"test-country-{number:02}" for number in expected
    ]
    assert [o.country_id for o in manifest.questions[0].options] == [
        "test-country-15",
        "test-country-10",
        "test-country-16",
        "test-country-05",
    ]
    for question in manifest.questions:
        assert len({option.country_id for option in question.options}) == 4
        assert question.options.count(question.correct_answer) == 1
        assert question.options[question.correct_answer_index] == question.correct_answer
    assert str(inputs.root).encode() not in raw
    assert b"generated_at" not in raw
    assert before == {path: path.read_bytes() for path in source_paths}
    assert sorted(path.name for path in first.parent.iterdir()) == ["first.json", "second.json"]


def test_existing_output_and_explicit_overwrite(inputs: SyntheticInputs) -> None:
    output = inputs.root / "manifest.json"
    output.write_bytes(b"previous output")
    result = CliRunner().invoke(app, arguments(inputs, output))
    assert result.exit_code == 1 and "--overwrite" in result.output
    assert output.read_bytes() == b"previous output"
    result = CliRunner().invoke(app, arguments(inputs, output, overwrite=True))
    assert result.exit_code == 0, result.output
    previous = output.read_bytes()
    result = CliRunner().invoke(app, arguments(inputs, output, overwrite=True))
    assert result.exit_code == 0 and output.read_bytes() == previous


@pytest.mark.parametrize(
    "failure", ["draft", "unverified", "missing", "corrupt", "malformed", "unknown"]
)
@pytest.mark.parametrize("existing", [False, True])
def test_bad_inputs_never_write_output(
    inputs: SyntheticInputs, failure: str, existing: bool
) -> None:
    output = inputs.root / "output/manifest.json"
    if existing:
        output.parent.mkdir()
        output.write_bytes(b"keep this output")
    if failure in {"draft", "unverified"}:
        data = json.loads(inputs.countries_path.read_bytes())
        if failure == "draft":
            data["editorial_status"] = "draft"
        else:
            data["countries"][0]["verification"]["flag"]["status"] = "needs_verification"
        inputs.countries_path.write_text(json.dumps(data), encoding="utf-8")
    elif failure == "missing":
        (inputs.root / "test-only.png").unlink()
    elif failure == "corrupt":
        (inputs.root / "test-only.png").write_bytes(b"corrupt")
    elif failure == "malformed":
        inputs.countries_path.write_text("{", encoding="utf-8")
    else:
        data = json.loads(inputs.recipe_path.read_bytes())
        data["candidate_country_ids"][0] = "unknown-country"
        inputs.recipe_path.write_text(json.dumps(data), encoding="utf-8")
    result = CliRunner().invoke(app, arguments(inputs, output, overwrite=True))
    assert result.exit_code == 1 and "Resolution failed" in result.output
    if existing:
        assert output.read_bytes() == b"keep this output"
        assert list(output.parent.iterdir()) == [output]
    else:
        assert not output.parent.exists()


@pytest.mark.parametrize("operation", ["create", "sync", "publish"])
@pytest.mark.parametrize("existing", [False, True])
def test_output_failures_preserve_previous_and_clean_temporary(
    inputs: SyntheticInputs,
    operation: str,
    existing: bool,
) -> None:
    output = inputs.root / "output/manifest.json"
    output.parent.mkdir()
    if existing:
        output.write_bytes(b"previous output")
    target = {
        "create": "quiztalcoatl.cli.tempfile.NamedTemporaryFile",
        "sync": "quiztalcoatl.cli.os.fsync",
        "publish": "quiztalcoatl.cli.os.replace" if existing else "quiztalcoatl.cli.os.link",
    }[operation]
    with patch(target, side_effect=OSError("simulated write failure")):
        result = CliRunner().invoke(app, arguments(inputs, output, overwrite=existing))
    assert result.exit_code == 1 and "simulated write failure" in result.output
    assert sorted(output.parent.iterdir()) == ([output] if existing else [])
    if existing:
        assert output.read_bytes() == b"previous output"


def test_serialization_failure_creates_no_directory(inputs: SyntheticInputs) -> None:
    output = inputs.root / "output/manifest.json"
    with patch(
        "quiztalcoatl.cli.ResolvedQuizManifest.model_dump_json",
        side_effect=ValueError("cannot serialize"),
    ):
        result = CliRunner().invoke(app, arguments(inputs, output))
    assert result.exit_code == 1 and "cannot serialize" in result.output
    assert not output.parent.exists()


def test_parent_path_failure(inputs: SyntheticInputs) -> None:
    parent = inputs.root / "blocked"
    parent.write_bytes(b"not a directory")
    result = CliRunner().invoke(app, arguments(inputs, parent / "manifest.json"))
    assert result.exit_code == 1 and "Resolution failed" in result.output
    assert parent.read_bytes() == b"not a directory"


def test_concurrent_output_creation_is_not_overwritten(inputs: SyntheticInputs) -> None:
    output = inputs.root / "output/manifest.json"
    link = os.link

    def competing_writer(source: Path, destination: Path) -> None:
        destination.write_bytes(b"concurrent output")
        link(source, destination)

    with patch("quiztalcoatl.cli.os.link", side_effect=competing_writer):
        result = CliRunner().invoke(app, arguments(inputs, output))
    assert result.exit_code == 1 and "--overwrite" in result.output
    assert output.read_bytes() == b"concurrent output"
    assert list(output.parent.iterdir()) == [output]


@pytest.mark.parametrize(
    "target", ["countries", "recipe", "flag", "unselected", "outline", "hardlink"]
)
def test_output_cannot_replace_inputs(inputs: SyntheticInputs, target: str) -> None:
    paths = {
        "countries": inputs.countries_path,
        "recipe": inputs.recipe_path,
        "flag": inputs.root / "test-only.png",
    }
    if target in {"unselected", "outline"}:
        asset_path = inputs.root / f"{target}.png"
        asset_path.write_bytes((inputs.root / "test-only.png").read_bytes())
        data = json.loads(inputs.countries_path.read_bytes())
        asset = data["countries"][0]["flag"].copy()
        asset["path"] = asset_path.name
        data["countries"][0]["flag" if target == "unselected" else "outline"] = asset
        inputs.countries_path.write_text(json.dumps(data), encoding="utf-8")
        output = asset_path
    elif target == "hardlink":
        output = inputs.root / "hardlink.json"
        os.link(inputs.countries_path, output)
    else:
        output = paths[target]
    before = output.read_bytes()
    result = CliRunner().invoke(app, arguments(inputs, output, overwrite=True))
    assert result.exit_code == 1 and "input JSON file or asset" in result.output
    assert output.read_bytes() == before


def test_real_editorial_state_controls_resolution(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    countries, recipe = root / "data/countries.json", root / "recipes/V-001.json"
    output = tmp_path / "real-output/manifest.json"
    result = CliRunner().invoke(
        app,
        [
            "resolve",
            "--countries",
            str(countries),
            "--recipe",
            str(recipe),
            "--content-root",
            str(root),
            "--output",
            str(output),
        ],
    )
    if load_snapshot(countries).editorial_status == "approved":
        assert result.exit_code == 0, result.output
        assert len(ResolvedQuizManifest.model_validate_json(output.read_bytes()).questions) == 15
    else:
        assert result.exit_code == 1 and "editorial approval" in result.output
        assert not output.parent.exists()


@pytest.mark.parametrize("existing", [False, True])
def test_partial_write_failure_is_cleaned(
    inputs: SyntheticInputs, existing: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = inputs.root / "output/manifest.json"
    output.parent.mkdir()
    if existing:
        output.write_bytes(b"previous output")
    factory = tempfile.NamedTemporaryFile

    def partial_file(**kwargs: Any) -> Any:
        stream = factory(**kwargs)
        write = stream.write

        def failing_write(data: str) -> int:
            write(data[:40])
            stream.flush()
            raise OSError("simulated disk full during write")

        monkeypatch.setattr(stream, "write", failing_write)
        return stream

    with patch("quiztalcoatl.cli.tempfile.NamedTemporaryFile", side_effect=partial_file):
        result = CliRunner().invoke(app, arguments(inputs, output, overwrite=existing))
    assert result.exit_code == 1 and "disk full" in result.output
    assert list(output.parent.iterdir()) == ([output] if existing else [])
    if existing:
        assert output.read_bytes() == b"previous output"


def test_unicode_serialization(inputs: SyntheticInputs) -> None:
    data = json.loads(inputs.countries_path.read_bytes())
    data["countries"][15]["name"] = "TEST ONLY: Côte d’Ivoire"
    inputs.countries_path.write_text(json.dumps(data), encoding="utf-8")
    output = inputs.root / "unicode.json"
    result = CliRunner().invoke(app, arguments(inputs, output))
    assert result.exit_code == 0, result.output
    assert "Côte d’Ivoire".encode() in output.read_bytes()
    ResolvedQuizManifest.model_validate_json(output.read_bytes())


def test_directory_and_dangling_symlink_are_protected(inputs: SyntheticInputs) -> None:
    directory = inputs.root / "output"
    directory.mkdir()
    result = CliRunner().invoke(app, arguments(inputs, directory, overwrite=True))
    assert result.exit_code == 1 and "directory" in result.output
    assert list(directory.iterdir()) == []
    output = directory / "link.json"
    output.symlink_to(inputs.root / "missing.json")
    result = CliRunner().invoke(app, arguments(inputs, output))
    assert result.exit_code == 1 and "--overwrite" in result.output
    assert output.is_symlink() and not output.exists()


def test_installed_cli_demonstration(inputs: SyntheticInputs) -> None:
    """Print an actual CLI run and repeatability hash; all content is test-only."""
    outputs = [inputs.root / "output/first.json", inputs.root / "output/second.json"]
    print("\nTEST ONLY: synthetic resolver CLI acceptance; not the real V-001 manifest")
    for output in outputs:
        result = subprocess.run(
            [sys.executable, "-m", "quiztalcoatl", *arguments(inputs, output)],
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        print(result.stdout.strip())
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    print(f"Byte-identical manifest SHA-256: {hashlib.sha256(outputs[0].read_bytes()).hexdigest()}")
    result = subprocess.run(
        [sys.executable, "-m", "quiztalcoatl", *arguments(inputs, outputs[0])],
        text=True,
        capture_output=True,
        timeout=10,
    )
    print(f"Overwrite refusal: exit {result.returncode}; {result.stderr.strip()}")
    assert result.returncode == 1 and "--overwrite" in result.stderr
