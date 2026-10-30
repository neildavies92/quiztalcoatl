"""Pure integer-frame V-001 pacing uses only synthetic approved manifest fixtures."""

from dataclasses import replace
from typing import Any, cast

import pytest
from pydantic import ValidationError
from test_resolver import SyntheticInputs, pure
from test_resolver import inputs as inputs

from quiztalcoatl.content import ContentError
from quiztalcoatl.timeline import build_timeline


def test_exact_full_timeline(inputs: SyntheticInputs) -> None:
    manifest = pure(inputs)
    timeline = build_timeline(manifest, content_root=inputs.root)
    assert timeline.fps == 30 and timeline.total_frames == 10650
    assert len(timeline.segments) == 34
    assert timeline.segments[0].kind == "intro"
    assert timeline.segments[0].start_frame == 0 and timeline.segments[0].duration_frames == 420
    assert timeline.segments[-1].kind == "outro"
    assert timeline.segments[-1].start_frame == 10110 and timeline.segments[-1].end_frame == 10650
    questions = [segment for segment in timeline.segments if segment.kind == "question"]
    reveals = [segment for segment in timeline.segments if segment.kind == "reveal"]
    assert [segment.question for segment in questions] == manifest.questions
    for question, reveal in zip(questions, reveals, strict=True):
        assert question.question == reveal.question
        assert question.duration_frames == 420 and reveal.duration_frames == 210
        assert question.end_frame == reveal.start_frame
        assert question.duration_frames + reveal.duration_frames == 630
    checkpoints = [segment for segment in timeline.segments if segment.kind == "checkpoint"]
    assert [segment.start_frame for segment in checkpoints] == [3570, 6840]
    assert [segment.question.ordinal for segment in checkpoints if segment.question] == [5, 10]
    for first, second in zip(timeline.segments, timeline.segments[1:], strict=False):
        assert first.end_frame == second.start_frame


@pytest.mark.parametrize(
    "failure",
    ["fps", "gap", "overlap", "duration", "total", "position", "pair", "order", "missing"],
)
def test_invalid_timeline_rejected(inputs: SyntheticInputs, failure: str) -> None:
    timeline = build_timeline(pure(inputs))
    segments = list(timeline.segments)
    if failure == "fps":
        with pytest.raises(ContentError, match="30 fps"):
            replace(timeline, fps=60)
        return
    if failure == "total":
        with pytest.raises(ContentError, match="total"):
            replace(timeline, total_frames=1)
        return
    if failure in {"gap", "overlap"}:
        segments[1] = replace(
            segments[1], start_frame=segments[1].start_frame + (1 if failure == "gap" else -1)
        )
    elif failure == "duration":
        segments[1] = replace(segments[1], duration_frames=-1)
    elif failure == "position":
        segments[1] = replace(segments[1], sequence=99)
    elif failure in {"pair", "order"}:
        segments[2 if failure == "pair" else 1] = replace(
            segments[2 if failure == "pair" else 1], question=pure(inputs).questions[1]
        )
    else:
        segments.pop()
    with pytest.raises(ContentError):
        replace(timeline, segments=tuple(segments))


def test_manifest_order_and_timing_requirements(inputs: SyntheticInputs) -> None:
    manifest = pure(inputs)
    with pytest.raises(ContentError, match="flag_identification"):
        build_timeline(manifest, quiz_format="capital_questions")
    with pytest.raises(ContentError, match="355-second"):
        build_timeline(manifest.model_copy(update={"video_id": "V-002"}))
    with pytest.raises(ValidationError):
        build_timeline(
            manifest.model_copy(update={"questions": list(reversed(manifest.questions))})
        )
    with pytest.raises(ValidationError):
        build_timeline(manifest.model_copy(update={"questions": []}))
    with pytest.raises(ContentError, match="missing asset"):
        (inputs.root / "test-only.png").unlink()
        build_timeline(manifest, content_root=inputs.root)


@pytest.mark.parametrize("field", ["sequence", "start_frame", "duration_frames"])
def test_frame_fields_reject_floats(inputs: SyntheticInputs, field: str) -> None:
    timeline = build_timeline(pure(inputs))
    segments = list(timeline.segments)
    changes: dict[str, Any] = {field: float(getattr(segments[0], field))}
    segments[0] = replace(segments[0], **changes)
    with pytest.raises(ContentError, match="integer frames"):
        replace(timeline, segments=tuple(segments))
    with pytest.raises(ContentError, match="integer"):
        replace(timeline, total_frames=cast(Any, 10650.0))
