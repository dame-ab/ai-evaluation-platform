import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes._access import (
    get_criterion_or_404,
    get_project_or_404,
    get_rubric_or_404,
)
from app.crud import create_rubric
from app.models import (
    Message,
    Rubric,
    RubricCreate,
    RubricCriterion,
    RubricCriterionCreate,
    RubricCriterionPublic,
    RubricCriterionUpdate,
    RubricPublic,
    RubricsPublic,
    RubricUpdate,
)

router = APIRouter(tags=["rubrics"])


@router.get("/projects/{project_id}/rubrics", response_model=RubricsPublic)
def read_rubrics(
    session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> Any:
    """List the scoring rubrics defined for a project."""
    get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    count = session.exec(
        select(func.count()).select_from(Rubric).where(Rubric.project_id == project_id)
    ).one()
    rubrics = session.exec(
        select(Rubric)
        .where(Rubric.project_id == project_id)
        .order_by(col(Rubric.created_at).asc())
    ).all()
    return RubricsPublic(data=rubrics, count=count)


@router.post("/projects/{project_id}/rubrics", response_model=RubricPublic)
def create_project_rubric(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    rubric_in: RubricCreate,
) -> Any:
    """Create a rubric (with an optional set of criteria) for a project."""
    get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )
    return create_rubric(session=session, rubric_in=rubric_in, project_id=project_id)


@router.get("/rubrics/{rubric_id}", response_model=RubricPublic)
def read_rubric(
    session: SessionDep, current_user: CurrentUser, rubric_id: uuid.UUID
) -> Any:
    """Get one rubric, including its criteria."""
    return get_rubric_or_404(
        session=session, rubric_id=rubric_id, current_user=current_user
    )


@router.put("/rubrics/{rubric_id}", response_model=RubricPublic)
def update_rubric(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rubric_id: uuid.UUID,
    rubric_in: RubricUpdate,
) -> Any:
    """Rename or redescribe a rubric."""
    rubric = get_rubric_or_404(
        session=session, rubric_id=rubric_id, current_user=current_user
    )
    update_dict = rubric_in.model_dump(exclude_unset=True)
    rubric.sqlmodel_update(update_dict)
    session.add(rubric)
    session.commit()
    session.refresh(rubric)
    return rubric


@router.delete("/rubrics/{rubric_id}")
def delete_rubric(
    session: SessionDep, current_user: CurrentUser, rubric_id: uuid.UUID
) -> Message:
    """Delete a rubric and its criteria."""
    rubric = get_rubric_or_404(
        session=session, rubric_id=rubric_id, current_user=current_user
    )
    session.delete(rubric)
    session.commit()
    return Message(message="Rubric deleted successfully")


@router.post("/rubrics/{rubric_id}/criteria", response_model=RubricCriterionPublic)
def add_criterion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rubric_id: uuid.UUID,
    criterion_in: RubricCriterionCreate,
) -> Any:
    """Add a scoring criterion (e.g. "Correctness") to a rubric."""
    get_rubric_or_404(session=session, rubric_id=rubric_id, current_user=current_user)
    criterion = RubricCriterion.model_validate(
        criterion_in, update={"rubric_id": rubric_id}
    )
    session.add(criterion)
    session.commit()
    session.refresh(criterion)
    return criterion


@router.put(
    "/rubrics/{rubric_id}/criteria/{criterion_id}",
    response_model=RubricCriterionPublic,
)
def update_criterion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rubric_id: uuid.UUID,
    criterion_id: uuid.UUID,
    criterion_in: RubricCriterionUpdate,
) -> Any:
    """Edit a rubric criterion's name, weight, description, or scale."""
    get_rubric_or_404(session=session, rubric_id=rubric_id, current_user=current_user)
    criterion = get_criterion_or_404(
        session=session, criterion_id=criterion_id, current_user=current_user
    )
    update_dict = criterion_in.model_dump(exclude_unset=True)
    criterion.sqlmodel_update(update_dict)
    session.add(criterion)
    session.commit()
    session.refresh(criterion)
    return criterion


@router.delete("/rubrics/{rubric_id}/criteria/{criterion_id}")
def delete_criterion(
    session: SessionDep,
    current_user: CurrentUser,
    rubric_id: uuid.UUID,
    criterion_id: uuid.UUID,
) -> Message:
    """Remove a criterion from a rubric."""
    get_rubric_or_404(session=session, rubric_id=rubric_id, current_user=current_user)
    criterion = get_criterion_or_404(
        session=session, criterion_id=criterion_id, current_user=current_user
    )
    session.delete(criterion)
    session.commit()
    return Message(message="Criterion deleted successfully")
