import uuid

from sqlmodel import Session

from app import crud
from app.models import (
    EvalTaskCreate,
    ModelResponseCreate,
    Project,
    ProjectCreate,
    Rubric,
    RubricCreate,
    RubricCriterionCreate,
)


def create_random_project(db: Session, owner_id: uuid.UUID) -> Project:
    project_in = ProjectCreate(name="Test Project", description="A project for tests")
    return crud.create_project(session=db, project_in=project_in, owner_id=owner_id)


def create_default_rubric(db: Session, project_id: uuid.UUID) -> Rubric:
    rubric_in = RubricCreate(
        name="Standard Rubric",
        description="Five-criterion evaluation rubric",
        criteria=[
            RubricCriterionCreate(name="Correctness", weight=1.5, max_score=5, order=0),
            RubricCriterionCreate(name="Relevance", weight=1.0, max_score=5, order=1),
            RubricCriterionCreate(name="Clarity", weight=1.0, max_score=5, order=2),
            RubricCriterionCreate(
                name="Completeness", weight=1.0, max_score=5, order=3
            ),
            RubricCriterionCreate(name="Safety", weight=1.5, max_score=5, order=4),
        ],
    )
    return crud.create_rubric(session=db, rubric_in=rubric_in, project_id=project_id)


def create_task_with_responses(
    db: Session, project_id: uuid.UUID, model_names: list[str]
) -> tuple:
    task = crud.create_task(
        session=db,
        task_in=EvalTaskCreate(
            title="Sample task",
            prompt="What is 2 + 2?",
            reference_answer="4",
            category="Math",
        ),
        project_id=project_id,
    )
    responses = [
        crud.create_response(
            session=db,
            response_in=ModelResponseCreate(
                model_name=model_name,
                response_text=f"The answer is 4, from {model_name}.",
            ),
            task_id=task.id,
        )
        for model_name in model_names
    ]
    return task, responses
