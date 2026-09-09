import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes._access import get_project_or_404
from app.models import (
    CriterionAverage,
    EvalTask,
    Evaluation,
    EvaluationScore,
    FailureBreakdownItem,
    ModelResponse,
    ModelWinRate,
    ProjectAnalytics,
    RubricCriterion,
)

router = APIRouter(tags=["analytics"])


@router.get("/projects/{project_id}/analytics", response_model=ProjectAnalytics)
def project_analytics(
    session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> Any:
    """Win-rate and score analytics for every model compared within a project."""
    get_project_or_404(
        session=session, project_id=project_id, current_user=current_user
    )

    total_tasks = session.exec(
        select(func.count())
        .select_from(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).one()
    total_responses = session.exec(
        select(func.count())
        .select_from(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).one()
    total_evaluations = session.exec(
        select(func.count())
        .select_from(Evaluation)
        .join(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).one()

    # Aggregated in Python rather than SQL: `is_winner` is a boolean and summing it
    # portably (SQLite vs. Postgres) is more trouble than it's worth at this scale,
    # and per-project evaluation counts are small enough that this stays fast.
    win_rate_rows = session.exec(
        select(ModelResponse.model_name, Evaluation.is_winner)
        .select_from(Evaluation)
        .join(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).all()

    win_rate_totals: dict[str, dict[str, int]] = {}
    for model_name, is_winner in win_rate_rows:
        bucket = win_rate_totals.setdefault(model_name, {"total": 0, "wins": 0})
        bucket["total"] += 1
        if is_winner:
            bucket["wins"] += 1

    win_rates = [
        ModelWinRate(
            model_name=model_name,
            evaluation_count=bucket["total"],
            win_count=bucket["wins"],
            win_rate=round(bucket["wins"] / bucket["total"], 4)
            if bucket["total"]
            else 0.0,
        )
        for model_name, bucket in sorted(
            win_rate_totals.items(), key=lambda item: item[0]
        )
    ]

    criterion_rows = session.exec(
        select(
            RubricCriterion.id,
            RubricCriterion.name,
            ModelResponse.model_name,
            EvaluationScore.score,
        )
        .select_from(EvaluationScore)
        .join(Evaluation, col(EvaluationScore.evaluation_id) == Evaluation.id)
        .join(ModelResponse, col(Evaluation.response_id) == ModelResponse.id)
        .join(EvalTask, col(ModelResponse.task_id) == EvalTask.id)
        .join(RubricCriterion, col(EvaluationScore.criterion_id) == RubricCriterion.id)
        .where(EvalTask.project_id == project_id)
    ).all()

    criterion_totals: dict[tuple[uuid.UUID, str, str], dict[str, float]] = {}
    for criterion_id, criterion_name, model_name, score in criterion_rows:
        criterion_key = (criterion_id, criterion_name, model_name)
        criterion_bucket = criterion_totals.setdefault(
            criterion_key, {"sum": 0.0, "count": 0}
        )
        criterion_bucket["sum"] += score
        criterion_bucket["count"] += 1

    criterion_averages = [
        CriterionAverage(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            model_name=model_name,
            average_score=round(criterion_bucket["sum"] / criterion_bucket["count"], 2),
            sample_count=int(criterion_bucket["count"]),
        )
        for (criterion_id, criterion_name, model_name), criterion_bucket in sorted(
            criterion_totals.items(), key=lambda item: (item[0][1], item[0][2])
        )
    ]

    failure_rows = session.exec(
        select(ModelResponse.model_name, Evaluation.failure_classification)
        .select_from(Evaluation)
        .join(ModelResponse)
        .join(EvalTask)
        .where(EvalTask.project_id == project_id)
    ).all()

    failure_totals: dict[tuple[str, str], int] = {}
    for model_name, classification in failure_rows:
        failure_key = (model_name, classification)
        failure_totals[failure_key] = failure_totals.get(failure_key, 0) + 1

    failure_breakdown = [
        FailureBreakdownItem(
            model_name=model_name, failure_classification=classification, count=count
        )
        for (model_name, classification), count in sorted(
            failure_totals.items(), key=lambda item: (item[0][0], item[0][1])
        )
    ]

    return ProjectAnalytics(
        total_tasks=total_tasks,
        total_responses=total_responses,
        total_evaluations=total_evaluations,
        win_rates=win_rates,
        criterion_averages=criterion_averages,
        failure_breakdown=failure_breakdown,
    )
