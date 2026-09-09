import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, delete, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes._access import get_response_or_404
from app.crud import create_evaluation
from app.models import (
    Evaluation,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationScore,
    EvaluationsPublic,
    EvaluationUpdate,
    Message,
    Rubric,
    RubricCriterion,
    ScoreInput,
)

router = APIRouter(tags=["evaluations"])


def _validate_rubric_and_scores(
    session: SessionDep,
    project_id: uuid.UUID,
    rubric_id: uuid.UUID,
    scores: list[ScoreInput],
) -> None:
    rubric = session.get(Rubric, rubric_id)
    if not rubric or rubric.project_id != project_id:
        raise HTTPException(
            status_code=400, detail="Rubric does not belong to this task's project"
        )
    criterion_ids = {c.criterion_id for c in scores}
    if not criterion_ids:
        return
    valid_ids = set(
        session.exec(
            select(RubricCriterion.id).where(RubricCriterion.rubric_id == rubric_id)
        ).all()
    )
    if not criterion_ids.issubset(valid_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more scored criteria do not belong to the chosen rubric",
        )


@router.get("/responses/{response_id}/evaluations", response_model=EvaluationsPublic)
def read_evaluations(
    session: SessionDep, current_user: CurrentUser, response_id: uuid.UUID
) -> Any:
    """List the evaluations recorded for a response."""
    get_response_or_404(
        session=session, response_id=response_id, current_user=current_user
    )
    count = session.exec(
        select(func.count())
        .select_from(Evaluation)
        .where(Evaluation.response_id == response_id)
    ).one()
    evaluations = session.exec(
        select(Evaluation)
        .where(Evaluation.response_id == response_id)
        .order_by(col(Evaluation.created_at).desc())
    ).all()
    return EvaluationsPublic(data=evaluations, count=count)


@router.post("/responses/{response_id}/evaluations", response_model=EvaluationPublic)
def add_evaluation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    response_id: uuid.UUID,
    evaluation_in: EvaluationCreate,
) -> Any:
    """Score a response: per-criterion scores, a written justification, an optional
    failure classification, and whether this response won the comparison."""
    response = get_response_or_404(
        session=session, response_id=response_id, current_user=current_user
    )
    assert response.task is not None  # guaranteed by the non-nullable task_id FK
    _validate_rubric_and_scores(
        session,
        response.task.project_id,
        evaluation_in.rubric_id,
        evaluation_in.scores,
    )
    return create_evaluation(
        session=session,
        evaluation_in=evaluation_in,
        response_id=response_id,
        evaluator_id=current_user.id,
    )


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationPublic)
def update_evaluation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    evaluation_id: uuid.UUID,
    evaluation_in: EvaluationUpdate,
) -> Any:
    """Edit an existing evaluation (only the evaluator or a superuser may)."""
    evaluation = session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if not current_user.is_superuser and evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_dict = evaluation_in.model_dump(exclude_unset=True, exclude={"scores"})
    evaluation.sqlmodel_update(update_dict)

    if evaluation_in.scores is not None:
        # Guaranteed by the non-nullable response_id/task_id FKs.
        assert evaluation.response is not None
        assert evaluation.response.task is not None
        _validate_rubric_and_scores(
            session,
            evaluation.response.task.project_id,
            evaluation.rubric_id,
            evaluation_in.scores,
        )
        # A bulk statement (rather than deleting each ORM-mapped object)
        # avoids leaving stale instances attached to `evaluation.scores`,
        # which would otherwise trip up the `session.add(evaluation)` below.
        session.exec(
            delete(EvaluationScore).where(
                col(EvaluationScore.evaluation_id) == evaluation.id
            )
        )
        session.flush()
        session.expire(evaluation, ["scores"])
        for score_in in evaluation_in.scores:
            session.add(
                EvaluationScore(
                    score=score_in.score,
                    criterion_id=score_in.criterion_id,
                    evaluation_id=evaluation.id,
                )
            )

    session.add(evaluation)
    session.commit()
    session.refresh(evaluation)
    return evaluation


@router.delete("/evaluations/{evaluation_id}")
def delete_evaluation(
    session: SessionDep, current_user: CurrentUser, evaluation_id: uuid.UUID
) -> Message:
    """Delete an evaluation (only the evaluator or a superuser may)."""
    evaluation = session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if not current_user.is_superuser and evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(evaluation)
    session.commit()
    return Message(message="Evaluation deleted successfully")
