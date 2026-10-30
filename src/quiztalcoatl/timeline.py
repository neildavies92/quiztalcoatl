"""Fixed V-001 pacing expressed exactly in integer video frames."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from quiztalcoatl.content import ContentError, check_asset
from quiztalcoatl.models import ResolvedQuestion, ResolvedQuizManifest

SegmentKind = Literal["intro", "question", "reveal", "checkpoint", "outro"]


@dataclass(frozen=True)
class Segment:
    sequence: int
    kind: SegmentKind
    start_frame: int
    duration_frames: int
    question: ResolvedQuestion | None = None

    @property
    def end_frame(self) -> int:
        return self.start_frame + self.duration_frames


@dataclass(frozen=True)
class Timeline:
    fps: int
    segments: tuple[Segment, ...]
    total_frames: int

    def __post_init__(self) -> None:
        if type(self.fps) is not int or self.fps != 30:
            raise ContentError("V-001 renderer supports only constant 30 fps")
        if not self.segments:
            raise ContentError("timeline must contain segments")
        if type(self.total_frames) is not int:
            raise ContentError("timeline total_frames must be an integer")
        cursor = 0
        for position, segment in enumerate(self.segments):
            if any(
                type(value) is not int
                for value in (segment.sequence, segment.start_frame, segment.duration_frames)
            ):
                raise ContentError("timeline sequence/start/duration must be integer frames")
            if segment.sequence != position or segment.start_frame != cursor:
                raise ContentError("timeline sequence has a gap, overlap or invalid position")
            if segment.duration_frames <= 0:
                raise ContentError("timeline segment durations must be positive")
            if segment.kind not in {"intro", "question", "reveal", "checkpoint", "outro"}:
                raise ContentError("unsupported timeline segment type")
            if segment.kind in {"question", "reveal", "checkpoint"} and segment.question is None:
                raise ContentError(
                    "question/reveal/checkpoint segment requires its content reference"
                )
            cursor = segment.end_frame
        kinds = [segment.kind for segment in self.segments]
        expected: list[SegmentKind] = ["intro"]
        for ordinal in range(1, 16):
            expected.extend(("question", "reveal"))
            if ordinal in (5, 10):
                expected.append("checkpoint")
        expected.append("outro")
        if kinds != expected:
            raise ContentError(
                "timeline must preserve all 15 question/reveal pairs and checkpoints"
            )
        ordinal = 0
        previous: ResolvedQuestion | None = None
        duration = {"intro": 420, "question": 420, "reveal": 210, "checkpoint": 120, "outro": 540}
        for segment in self.segments:
            if segment.duration_frames != duration[segment.kind]:
                raise ContentError("timeline segment violates fixed V-001 pacing")
            if segment.kind == "question":
                ordinal += 1
                if segment.question is None or segment.question.ordinal != ordinal:
                    raise ContentError("timeline question order is invalid")
                previous = segment.question
            elif segment.kind in {"reveal", "checkpoint"} and segment.question != previous:
                raise ContentError(
                    "timeline reveal/checkpoint reference does not match its question"
                )
        if cursor != self.total_frames:
            raise ContentError("timeline total does not match its segment frames")


def build_timeline(
    manifest: ResolvedQuizManifest,
    *,
    content_root: Path | None = None,
    fps: int = 30,
    quiz_format: str = "flag_identification",
) -> Timeline:
    """Preserve manifest order; optionally check local assets without running FFmpeg."""
    if quiz_format != "flag_identification":
        raise ContentError("only flag_identification is supported")
    manifest = ResolvedQuizManifest.model_validate_json(manifest.model_dump_json())
    timing = manifest.timing
    if (
        manifest.video_id != "V-001"
        or len(manifest.questions) != 15
        or timing.question_seconds != 21
        or timing.intro_seconds != 14
        or timing.checkpoint_seconds != 4
        or timing.checkpoint_after != [5, 10]
        or timing.outro_seconds != 18
        or manifest.expected_total_seconds != 355
    ):
        raise ContentError(
            "initial renderer requires V-001: 15 questions and fixed 355-second timing"
        )
    segments: list[Segment] = []
    cursor = 0

    def append(kind: SegmentKind, seconds: int, question: ResolvedQuestion | None = None) -> None:
        nonlocal cursor
        frames = seconds * 30
        segments.append(Segment(len(segments), kind, cursor, frames, question))
        cursor += frames

    append("intro", 14)
    for question in manifest.questions:
        if content_root is not None:
            check_asset(question.asset, content_root, required=True, png=True)
        append("question", 14, question)
        append("reveal", 7, question)
        if question.ordinal in timing.checkpoint_after:
            append("checkpoint", 4, question)
    append("outro", 18)
    return Timeline(fps, tuple(segments), 10650)
