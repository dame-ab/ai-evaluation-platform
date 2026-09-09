"""Ownership-checking helpers shared by the evaluation-domain routers.

Every domain object (rubric, task, response, evaluation) hangs off a
`Project`, and a `Project` belongs to the user who created it. These helpers
walk that chain, returning 404 when an object doesn't exist and 403 when the
current user doesn't own the owning project (superusers can access
everything, mirroring the template's admin model).
"""

import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.models import EvalTask, ModelResponse, Project, Rubric, RubricCriterion, User


def get_project_or_404(
    *, session: Session, project_id: uuid.UUID, current_user: User
) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return project


def get_rubric_or_404(
    *, session: Session, rubric_id: uuid.UUID, current_user: User
) -> Rubric:
    rubric = session.get(Rubric, rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    get_project_or_404(
        session=session, project_id=rubric.project_id, current_user=current_user
    )
    return rubric


def get_criterion_or_404(
    *, session: Session, criterion_id: uuid.UUID, current_user: User
) -> RubricCriterion:
    criterion = session.get(RubricCriterion, criterion_id)
    if not criterion:
        raise HTTPException(status_code=404, detail="Rubric criterion not found")
    get_rubric_or_404(
        session=session, rubric_id=criterion.rubric_id, current_user=current_user
    )
    return criterion


def get_task_or_404(
    *, session: Session, task_id: uuid.UUID, current_user: User
) -> EvalTask:
    task = session.get(EvalTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    get_project_or_404(
        session=session, project_id=task.project_id, current_user=current_user
    )
    return task


def get_response_or_404(
    *, session: Session, response_id: uuid.UUID, current_user: User
) -> ModelResponse:
    response = session.get(ModelResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Model response not found")
    get_task_or_404(
        session=session, task_id=response.task_id, current_user=current_user
    )
    return response
