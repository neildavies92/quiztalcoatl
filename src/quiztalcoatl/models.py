"""Version-one editorial inputs and resolved renderer contracts."""

from datetime import date
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
VideoId = Annotated[str, StringConstraints(pattern=r"^V-[0-9]{3}$")]
Checksum = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
PositiveInt = Annotated[int, Field(gt=0)]
Seconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class VersionedContract(Contract):
    schema_version: Literal[1]

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            raise ValueError("schema_version must be integer 1")
        return value


class SourceReference(Contract):
    url: HttpUrl
    title: Text | None = None
    accessed_on: date | None = None


class AssetReference(Contract):
    path: Text
    sha256: Checksum
    source_url: HttpUrl
    licence: Text
    attribution: Text | None = None
    notes: Text | None = None

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or PureWindowsPath(value).drive
            or "\\" in value
            or ".." in path.parts
            or value == "."
            or "\x00" in value
        ):
            raise ValueError("asset path must be a relative POSIX path without traversal")
        return value


class CapitalCity(Contract):
    name: Text
    role: Text | None = None
    notes: Text | None = None


class VerificationRecord(Contract):
    status: Literal["needs_verification", "verified"]
    sources: list[SourceReference]
    verified_by: Text | None = None
    verified_on: date | None = None

    @model_validator(mode="after")
    def complete_review(self) -> Self:
        if self.status == "verified" and not (
            self.sources and self.verified_by and self.verified_on
        ):
            raise ValueError("verified records require sources, verified_by and verified_on")
        return self


class Eligibility(Contract):
    flag_identification: bool
    capital_questions: bool
    outline_identification: bool


class CountryVerification(Contract):
    identity: VerificationRecord
    capitals: VerificationRecord | None = None
    flag: VerificationRecord | None = None
    outline: VerificationRecord | None = None
    flag_learning_fact: VerificationRecord | None = None


class LearningFact(Contract):
    text: Annotated[str, StringConstraints(min_length=1, max_length=500, pattern=r"\S")]
    sources: list[SourceReference] = Field(min_length=1)


class CountryRecord(Contract):
    country_id: Identifier
    name: Text
    continent: Text
    region: Text
    capitals: list[CapitalCity]
    flag: AssetReference | None = None
    outline: AssetReference | None = None
    flag_learning_fact: LearningFact | None = None
    eligibility: Eligibility
    verification: CountryVerification
    notes: Text | None = None

    @model_validator(mode="after")
    def capital_eligibility(self) -> Self:
        if self.eligibility.capital_questions and len(self.capitals) != 1:
            raise ValueError("simple capital_questions eligibility requires exactly one capital")
        return self


def unique(values: list[str], label: str) -> None:
    normalized = [" ".join(value.split()).casefold() for value in values]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} must be unique (ignoring case and whitespace)")


class CountrySnapshot(VersionedContract):
    snapshot_id: Identifier
    editorial_status: Literal["draft", "approved"]
    approved_by: Text | None = None
    approved_on: date | None = None
    countries: list[CountryRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def snapshot_consistency(self) -> Self:
        unique([country.country_id for country in self.countries], "country IDs")
        unique([country.name for country in self.countries], "country display names")
        if self.editorial_status == "approved" and not (self.approved_by and self.approved_on):
            raise ValueError("approved snapshots require approved_by and approved_on")
        return self


class Timing(Contract):
    question_seconds: Literal[21]
    intro_seconds: Seconds
    checkpoint_seconds: Seconds
    checkpoint_after: list[PositiveInt]
    outro_seconds: Seconds

    @field_validator("question_seconds", mode="before")
    @classmethod
    def exact_cycle(cls, value: object) -> object:
        if type(value) is not int or value != 21:
            raise ValueError("question_seconds must be integer 21")
        return value

    @model_validator(mode="after")
    def ordered_checkpoints(self) -> Self:
        if self.checkpoint_after != sorted(set(self.checkpoint_after)):
            raise ValueError("checkpoint_after must contain unique ascending ordinals")
        return self

    def total_seconds(self, question_count: int) -> float:
        if any(ordinal >= question_count for ordinal in self.checkpoint_after):
            raise ValueError("checkpoints must occur before the final question")
        return (
            self.intro_seconds
            + question_count * self.question_seconds
            + len(self.checkpoint_after) * self.checkpoint_seconds
            + self.outro_seconds
        )


class Publication(Contract):
    working_title: Text
    thumbnail_hook: Text


class QuizRecipe(VersionedContract):
    video_id: VideoId
    topic: Literal["Geography"]
    quiz_format: Literal["flag_identification"]
    difficulty: Literal["Easy"]
    scope: Literal["World"]
    question_count: PositiveInt
    candidate_country_ids: list[Identifier]
    seed: int
    distractor_count: Literal[3]
    timing: Timing
    theme_id: Identifier
    publication: Publication

    @field_validator("distractor_count", mode="before")
    @classmethod
    def exact_distractors(cls, value: object) -> object:
        if type(value) is not int or value != 3:
            raise ValueError("distractor_count must be integer 3")
        return value

    @model_validator(mode="after")
    def recipe_consistency(self) -> Self:
        unique(self.candidate_country_ids, "candidate_country_ids")
        if len(self.candidate_country_ids) < max(self.question_count, self.distractor_count + 1):
            raise ValueError("insufficient candidate pool for questions and three distractors")
        if self.video_id == "V-001" and self.question_count != 15:
            raise ValueError("V-001 requires exactly 15 questions")
        self.timing.total_seconds(self.question_count)
        return self


class AnswerOption(Contract):
    country_id: Identifier
    label: Text


class ResolvedQuestion(Contract):
    ordinal: PositiveInt
    question_id: Identifier
    prompt: Text
    correct_answer: AnswerOption
    options: list[AnswerOption] = Field(min_length=4, max_length=4)
    correct_answer_index: Annotated[int, Field(ge=0, le=3)]
    asset: AssetReference
    explanation: LearningFact
    sources: list[SourceReference] = Field(min_length=1)

    @model_validator(mode="after")
    def answer_consistency(self) -> Self:
        unique([option.country_id for option in self.options], "answer option IDs")
        unique([option.label for option in self.options], "answer option labels")
        if self.options[self.correct_answer_index] != self.correct_answer:
            raise ValueError("correct_answer must match the option at correct_answer_index")
        return self


class ResolvedQuizManifest(VersionedContract):
    video_id: VideoId
    questions: list[ResolvedQuestion] = Field(min_length=1)
    recipe_sha256: Checksum
    snapshot_sha256: Checksum
    seed: int
    theme_id: Identifier
    timing: Timing
    expected_total_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)]

    @model_validator(mode="after")
    def manifest_consistency(self) -> Self:
        unique([question.question_id for question in self.questions], "question IDs")
        if [question.ordinal for question in self.questions] != list(
            range(1, len(self.questions) + 1)
        ):
            raise ValueError("question ordinals must be consecutive and ordered from 1")
        if self.video_id == "V-001" and len(self.questions) != 15:
            raise ValueError("V-001 requires exactly 15 resolved questions")
        if abs(self.expected_total_seconds - self.timing.total_seconds(len(self.questions))) > 1e-6:
            raise ValueError("expected_total_seconds does not match timing and question count")
        return self
