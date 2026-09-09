import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes._access import (
    get_project_or_404,
    get_response_or_404,
    get_task_or_404,
)
from app.crud import create_response, create_task
from app.models import (
    EvalTask,
    EvalTaskCreate,
    EvalTasksPublic,
    EvalTaskSummary,
    EvalTaskUpdate,
    Evaluation,
    Message,
    ModelResponse,
    ModelResponseCreate,
    ModelResponsePublic,
    ModelResponsesPublic,
    ModelResponseUpdate,
)

router = APIRouter(tags=["tasks"])


def _summarize_task(session: SessionDep, task: EvalTask) -> EvalTaskSummary:
    response_count = session.exec(
        select(func.count())
        .select_from(ModelResponse)
        .where(ModelResponse.task_id == task.id)
    ).one()
    evaluation_count = session.exec(
        select(func.count())
        .select_from(Evaluation)
        .join(ModelResponse)
        .where(ModelResponse.task_id == task.id)
    ).one()
    return EvalTaskSummary(
        **task.model_dump(),
        response_count=response_count,
        evaluation_count=evaluation_count,
    )


@router.get("/projects/{project_id}/tasks", response_model=EvalTasksPublic)
def read_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List the evaluation tasks (prompts) in a project."""
    get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    count = session.exec(
        select(func.count())
        .select_from(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).one()
    tasks = session.exec(
        select(EvalTask)
        .where(EvalTask.project_id == project_id)
        .order_by(col(EvalTask.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return EvalTasksPublic(
        data=[_summarize_task(session, task) for task in tasks], count=count
    )


@router.post("/projects/{project_id}/tasks", response_model=EvalTaskSummary)
def create_project_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    task_in: EvalTaskCreate,
) -> Any:
    """Add a new task (prompt to be evaluated across models) to a project."""
    get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    task = create_task(session=session, task_in=task_in, project_id=project_id)
    return _summarize_task(session, task)


@router.get("/tasks/{task_id}", response_model=EvalTaskSummary)
def read_task(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID
) -> Any:
    """Get one task."""
    task = get_task_or_404(session=session, task_id=task_id, current_user=current_user)
    return _summarize_task(session, task)


@router.put("/tasks/{task_id}", response_model=EvalTaskSummary)
def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    task_in: EvalTaskUpdate,
) -> Any:
    """Edit a task's prompt, reference answer, or category."""
    task = get_task_or_404(session=session, task_id=task_id, current_user=current_user)
    update_dict = task_in.model_dump(exclude_unset=True)
    task.sqlmodel_update(update_dict)
    session.add(task)
    session.commit()
    session.refresh(task)
    return _summarize_task(session, task)


@router.delete("/tasks/{task_id}")
def delete_task(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID
) -> Message:
    """Delete a task and its responses/evaluations."""
    task = get_task_or_404(session=session, task_id=task_id, current_user=current_user)
    session.delete(task)
    session.commit()
    return Message(message="Task deleted successfully")


@router.get("/tasks/{task_id}/responses", response_model=ModelResponsesPublic)
def read_responses(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID
) -> Any:
    """List the model responses submitted for a task, for side-by-side comparison."""
    get_task_or_404(session=session, task_id=task_id, current_user=current_user)
    count = session.exec(
        select(func.count())
        .select_from(ModelResponse)
        .where(ModelResponse.task_id == task_id)
    ).one()
    responses = session.exec(
        select(ModelResponse)
        .where(ModelResponse.task_id == task_id)
        .order_by(col(ModelResponse.created_at).asc())
    ).all()
    return ModelResponsesPublic(data=responses, count=count)


@router.post("/tasks/{task_id}/responses", response_model=ModelResponsePublic)
def add_response(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    response_in: ModelResponseCreate,
) -> Any:
    """Record a model's response to a task's prompt."""
    get_task_or_404(session=session, task_id=task_id, current_user=current_user)
    return create_response(session=session, response_in=response_in, task_id=task_id)


@router.put("/responses/{response_id}", response_model=ModelResponsePublic)
def update_response(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    response_id: uuid.UUID,
    response_in: ModelResponseUpdate,
) -> Any:
    """Edit a recorded model response."""
    response = get_response_or_404(
        session=session, response_id=response_id, current_user=current_user
    )
    update_dict = response_in.model_dump(exclude_unset=True)
    response.sqlmodel_update(update_dict)
    session.add(response)
    session.commit()
    session.refresh(response)
    return response


@router.delete("/responses/{response_id}")
def delete_response(
    session: SessionDep, current_user: CurrentUser, response_id: uuid.UUID
) -> Message:
    """Delete a model response and any evaluations of it."""
    response = get_response_or_404(
        session=session, response_id=response_id, current_user=current_user
    )
    session.delete(response)
    session.commit()
    return Message(message="Response deleted successfully")
