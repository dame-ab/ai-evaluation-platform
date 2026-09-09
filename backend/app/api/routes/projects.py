import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes._access import get_project_or_404
from app.crud import create_project
from app.models import (
    EvalTask,
    Evaluation,
    Message,
    ModelResponse,
    Project,
    ProjectCreate,
    ProjectsPublic,
    ProjectSummary,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _summarize(session: SessionDep, project: Project) -> ProjectSummary:
    task_count = session.exec(
        select(func.count())
        .select_from(EvalTask)
        .where(EvalTask.project_id == project.id)
    ).one()
    response_count = session.exec(
        select(func.count())
        .select_from(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project.id)
    ).one()
    evaluation_count = session.exec(
        select(func.count())
        .select_from(Evaluation)
        .join(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project.id)
    ).one()
    return ProjectSummary(
        **project.model_dump(),
        task_count=task_count,
        response_count=response_count,
        evaluation_count=evaluation_count,
    )


@router.get("/", response_model=ProjectsPublic)
def read_projects(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve the current user's evaluation projects (all projects for a superuser)."""
    base = select(Project)
    count_base = select(func.count()).select_from(Project)
    if not current_user.is_superuser:
        base = base.where(Project.owner_id == current_user.id)
        count_base = count_base.where(Project.owner_id == current_user.id)

    count = session.exec(count_base).one()
    statement = base.order_by(col(Project.created_at).desc()).offset(skip).limit(limit)
    projects = session.exec(statement).all()

    return ProjectsPublic(
        data=[_summarize(session, project) for project in projects], count=count
    )


@router.get("/{project_id}", response_model=ProjectSummary)
def read_project(
    session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> Any:
    """Get one project by ID, with rollup counts."""
    project = get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    return _summarize(session, project)


@router.post("/", response_model=ProjectSummary)
def create_new_project(
    *, session: SessionDep, current_user: CurrentUser, project_in: ProjectCreate
) -> Any:
    """Create a new evaluation project."""
    project = create_project(
        session=session, project_in=project_in, owner_id=current_user.id
    )
    return _summarize(session, project)


@router.put("/{project_id}", response_model=ProjectSummary)
def update_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
) -> Any:
    """Update a project's name/description."""
    project = get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    update_dict = project_in.model_dump(exclude_unset=True)
    project.sqlmodel_update(update_dict)
    session.add(project)
    session.commit()
    session.refresh(project)
    return _summarize(session, project)


@router.delete("/{project_id}")
def delete_project(
    session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> Message:
    """Delete a project and everything nested under it (rubrics, tasks, responses, evaluations)."""
    project = get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    session.delete(project)
    session.commit()
    return Message(message="Project deleted successfully")
