import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    EvalTask,
    EvalTaskCreate,
    Evaluation,
    EvaluationCreate,
    EvaluationScore,
    ModelResponse,
    ModelResponseCreate,
    Project,
    ProjectCreate,
    Rubric,
    RubricCreate,
    RubricCriterion,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def create_project(
    *, session: Session, project_in: ProjectCreate, owner_id: uuid.UUID
) -> Project:
    db_project = Project.model_validate(project_in, update={"owner_id": owner_id})
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


# ---------------------------------------------------------------------------
# Rubrics & criteria
# ---------------------------------------------------------------------------


def create_rubric(
    *, session: Session, rubric_in: RubricCreate, project_id: uuid.UUID
) -> Rubric:
    db_rubric = Rubric(
        name=rubric_in.name, description=rubric_in.description, project_id=project_id
    )
    session.add(db_rubric)
    session.flush()
    for index, criterion_in in enumerate(rubric_in.criteria):
        criterion = RubricCriterion.model_validate(
            criterion_in,
            update={"rubric_id": db_rubric.id, "order": criterion_in.order or index},
        )
        session.add(criterion)
    session.commit()
    session.refresh(db_rubric)
    return db_rubric


# ---------------------------------------------------------------------------
# Tasks & responses
# ---------------------------------------------------------------------------


def create_task(
    *, session: Session, task_in: EvalTaskCreate, project_id: uuid.UUID
) -> EvalTask:
    db_task = EvalTask.model_validate(task_in, update={"project_id": project_id})
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def create_response(
    *, session: Session, response_in: ModelResponseCreate, task_id: uuid.UUID
) -> ModelResponse:
    db_response = ModelResponse.model_validate(response_in, update={"task_id": task_id})
    session.add(db_response)
    session.commit()
    session.refresh(db_response)
    return db_response


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------


def create_evaluation(
    *,
    session: Session,
    evaluation_in: EvaluationCreate,
    response_id: uuid.UUID,
    evaluator_id: uuid.UUID,
) -> Evaluation:
    db_evaluation = Evaluation(
        justification=evaluation_in.justification,
        failure_classification=evaluation_in.failure_classification,
        is_winner=evaluation_in.is_winner,
        rubric_id=evaluation_in.rubric_id,
        response_id=response_id,
        evaluator_id=evaluator_id,
    )
    session.add(db_evaluation)
    session.flush()
    for score_in in evaluation_in.scores:
        score = EvaluationScore(
            score=score_in.score,
            criterion_id=score_in.criterion_id,
            evaluation_id=db_evaluation.id,
        )
        session.add(score)
    session.commit()
    session.refresh(db_evaluation)
    return db_evaluation
