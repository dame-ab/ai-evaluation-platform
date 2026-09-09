import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Users & auth
# ---------------------------------------------------------------------------


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    projects: list[Project] = Relationship(back_populates="owner", cascade_delete=True)
    evaluations: list[Evaluation] = Relationship(back_populates="evaluator")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class Project(ProjectBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner: User | None = Relationship(back_populates="projects")
    rubrics: list[Rubric] = Relationship(back_populates="project", cascade_delete=True)
    tasks: list[EvalTask] = Relationship(back_populates="project", cascade_delete=True)


class ProjectPublic(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ProjectSummary(ProjectPublic):
    """A project annotated with lightweight counts, used for list views."""

    task_count: int = 0
    response_count: int = 0
    evaluation_count: int = 0


class ProjectsPublic(SQLModel):
    data: list[ProjectSummary]
    count: int


# ---------------------------------------------------------------------------
# Rubrics & criteria
# ---------------------------------------------------------------------------


class RubricCriterionBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    weight: float = Field(default=1.0, ge=0, le=10)
    max_score: int = Field(default=5, ge=1, le=100)
    order: int = Field(default=0, ge=0)


class RubricCriterionCreate(RubricCriterionBase):
    pass


class RubricCriterionUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    weight: float | None = Field(default=None, ge=0, le=10)
    max_score: int | None = Field(default=None, ge=1, le=100)
    order: int | None = Field(default=None, ge=0)


class RubricCriterion(RubricCriterionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rubric_id: uuid.UUID = Field(
        foreign_key="rubric.id", nullable=False, ondelete="CASCADE"
    )
    rubric: Rubric = Relationship(back_populates="criteria")
    scores: list[EvaluationScore] = Relationship(
        back_populates="criterion", cascade_delete=True
    )


class RubricCriterionPublic(RubricCriterionBase):
    id: uuid.UUID
    rubric_id: uuid.UUID


class RubricBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class RubricCreate(RubricBase):
    criteria: list[RubricCriterionCreate] = Field(default_factory=list)


class RubricUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class Rubric(RubricBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="project.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    project: Project | None = Relationship(back_populates="rubrics")
    criteria: list[RubricCriterion] = Relationship(
        back_populates="rubric", cascade_delete=True
    )
    evaluations: list[Evaluation] = Relationship(back_populates="rubric")


class RubricPublic(RubricBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime | None = None
    criteria: list[RubricCriterionPublic] = Field(default_factory=list)


class RubricsPublic(SQLModel):
    data: list[RubricPublic]
    count: int


# ---------------------------------------------------------------------------
# Evaluation tasks (a prompt evaluated across several model responses)
# ---------------------------------------------------------------------------


class EvalTaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    prompt: str = Field(min_length=1, max_length=8000)
    reference_answer: str | None = Field(default=None, max_length=8000)
    category: str | None = Field(default=None, max_length=100)


class EvalTaskCreate(EvalTaskBase):
    pass


class EvalTaskUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    prompt: str | None = Field(default=None, min_length=1, max_length=8000)
    reference_answer: str | None = Field(default=None, max_length=8000)
    category: str | None = Field(default=None, max_length=100)


class EvalTask(EvalTaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="project.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    project: Project | None = Relationship(back_populates="tasks")
    responses: list[ModelResponse] = Relationship(
        back_populates="task", cascade_delete=True
    )


class EvalTaskPublic(EvalTaskBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime | None = None


class EvalTaskSummary(EvalTaskPublic):
    response_count: int = 0
    evaluation_count: int = 0


class EvalTasksPublic(SQLModel):
    data: list[EvalTaskSummary]
    count: int


# ---------------------------------------------------------------------------
# Model responses (one AI system's answer to a task, for side-by-side compare)
# ---------------------------------------------------------------------------


class ModelResponseBase(SQLModel):
    model_name: str = Field(min_length=1, max_length=100)
    response_text: str = Field(min_length=1, max_length=8000)


class ModelResponseCreate(ModelResponseBase):
    pass


class ModelResponseUpdate(SQLModel):
    model_name: str | None = Field(default=None, min_length=1, max_length=100)
    response_text: str | None = Field(default=None, min_length=1, max_length=8000)


class ModelResponse(ModelResponseBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(
        foreign_key="evaltask.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    task: EvalTask | None = Relationship(back_populates="responses")
    evaluations: list[Evaluation] = Relationship(
        back_populates="response", cascade_delete=True
    )


class ModelResponsePublic(ModelResponseBase):
    id: uuid.UUID
    task_id: uuid.UUID
    created_at: datetime | None = None


class ModelResponsesPublic(SQLModel):
    data: list[ModelResponsePublic]
    count: int


# ---------------------------------------------------------------------------
# Evaluations (an evaluator's judgement of one response, against a rubric)
# ---------------------------------------------------------------------------


class FailureClassification(StrEnum):
    NONE = "none"
    HALLUCINATION = "hallucination"
    FACTUAL_ERROR = "factual_error"
    INCOMPLETE_ANSWER = "incomplete_answer"
    UNSAFE_CONTENT = "unsafe_content"
    OFF_TOPIC = "off_topic"
    FORMATTING_ERROR = "formatting_error"
    OTHER = "other"


class ScoreInput(SQLModel):
    criterion_id: uuid.UUID
    score: float = Field(ge=0, le=100)


class EvaluationBase(SQLModel):
    justification: str | None = Field(default=None, max_length=4000)
    failure_classification: FailureClassification = FailureClassification.NONE
    is_winner: bool = False


class EvaluationCreate(EvaluationBase):
    rubric_id: uuid.UUID
    scores: list[ScoreInput] = Field(default_factory=list)


class EvaluationUpdate(SQLModel):
    justification: str | None = Field(default=None, max_length=4000)
    failure_classification: FailureClassification | None = None
    is_winner: bool | None = None
    scores: list[ScoreInput] | None = None


class Evaluation(EvaluationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    response_id: uuid.UUID = Field(
        foreign_key="modelresponse.id", nullable=False, ondelete="CASCADE"
    )
    evaluator_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    rubric_id: uuid.UUID = Field(foreign_key="rubric.id", nullable=False)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    response: ModelResponse | None = Relationship(back_populates="evaluations")
    evaluator: User | None = Relationship(back_populates="evaluations")
    rubric: Rubric | None = Relationship(back_populates="evaluations")
    scores: list[EvaluationScore] = Relationship(
        back_populates="evaluation", cascade_delete=True
    )


class EvaluationScoreBase(SQLModel):
    score: float = Field(ge=0, le=100)


class EvaluationScore(EvaluationScoreBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    evaluation_id: uuid.UUID = Field(
        foreign_key="evaluation.id", nullable=False, ondelete="CASCADE"
    )
    criterion_id: uuid.UUID = Field(
        foreign_key="rubriccriterion.id", nullable=False, ondelete="CASCADE"
    )
    evaluation: Evaluation | None = Relationship(back_populates="scores")
    criterion: RubricCriterion | None = Relationship(back_populates="scores")


class EvaluationScorePublic(EvaluationScoreBase):
    id: uuid.UUID
    criterion_id: uuid.UUID


class EvaluationPublic(EvaluationBase):
    id: uuid.UUID
    response_id: uuid.UUID
    evaluator_id: uuid.UUID
    rubric_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    scores: list[EvaluationScorePublic] = Field(default_factory=list)


class EvaluationsPublic(SQLModel):
    data: list[EvaluationPublic]
    count: int


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class ModelWinRate(SQLModel):
    model_name: str
    evaluation_count: int
    win_count: int
    win_rate: float


class CriterionAverage(SQLModel):
    criterion_id: uuid.UUID
    criterion_name: str
    model_name: str
    average_score: float
    sample_count: int


class FailureBreakdownItem(SQLModel):
    model_name: str
    failure_classification: FailureClassification
    count: int


class ProjectAnalytics(SQLModel):
    total_tasks: int
    total_responses: int
    total_evaluations: int
    win_rates: list[ModelWinRate]
    criterion_averages: list[CriterionAverage]
    failure_breakdown: list[FailureBreakdownItem]


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
