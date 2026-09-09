"""End-to-end coverage of the core product flow: define a rubric, add a task
with competing model responses, score them, and confirm the analytics
rollup reflects the scores -- the same path the frontend's comparison and
analytics views drive through the API.
"""

from fastapi.testclient import TestClient

from app.core.config import settings

RUBRIC_CRITERIA = [
    {"name": "Correctness", "weight": 1.5, "max_score": 5, "order": 0},
    {"name": "Safety", "weight": 1.5, "max_score": 5, "order": 1},
]


def _create_project(client: TestClient, headers: dict) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=headers,
        json={"name": "Workflow Test Project", "description": None},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_rubric(client: TestClient, headers: dict, project_id: str) -> dict:
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/rubrics",
        headers=headers,
        json={"name": "Rubric", "description": None, "criteria": RUBRIC_CRITERIA},
    )
    assert r.status_code == 200
    return r.json()


def _create_task(client: TestClient, headers: dict, project_id: str) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/tasks",
        headers=headers,
        json={
            "title": "Sample prompt",
            "prompt": "Explain photosynthesis simply.",
            "reference_answer": "Plants convert light into energy.",
            "category": "Science",
        },
    )
    assert r.status_code == 200
    return r.json()["id"]


def _add_response(
    client: TestClient, headers: dict, task_id: str, model_name: str
) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/tasks/{task_id}/responses",
        headers=headers,
        json={"model_name": model_name, "response_text": f"Answer from {model_name}."},
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_full_evaluation_workflow_and_analytics(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)
    rubric = _create_rubric(client, headers, project_id)
    criteria_by_name = {c["name"]: c["id"] for c in rubric["criteria"]}
    task_id = _create_task(client, headers, project_id)

    good_response_id = _add_response(client, headers, task_id, "Strong Model")
    weak_response_id = _add_response(client, headers, task_id, "Weak Model")

    r = client.post(
        f"{settings.API_V1_STR}/responses/{good_response_id}/evaluations",
        headers=headers,
        json={
            "rubric_id": rubric["id"],
            "justification": "Accurate and safe.",
            "failure_classification": "none",
            "is_winner": True,
            "scores": [
                {"criterion_id": criteria_by_name["Correctness"], "score": 5},
                {"criterion_id": criteria_by_name["Safety"], "score": 5},
            ],
        },
    )
    assert r.status_code == 200
    evaluation = r.json()
    assert evaluation["is_winner"] is True
    assert len(evaluation["scores"]) == 2

    r = client.post(
        f"{settings.API_V1_STR}/responses/{weak_response_id}/evaluations",
        headers=headers,
        json={
            "rubric_id": rubric["id"],
            "justification": "Got the core fact wrong.",
            "failure_classification": "factual_error",
            "is_winner": False,
            "scores": [
                {"criterion_id": criteria_by_name["Correctness"], "score": 1},
                {"criterion_id": criteria_by_name["Safety"], "score": 4},
            ],
        },
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/projects/{project_id}/analytics", headers=headers
    )
    assert r.status_code == 200
    analytics = r.json()
    assert analytics["total_tasks"] == 1
    assert analytics["total_responses"] == 2
    assert analytics["total_evaluations"] == 2

    win_rates = {w["model_name"]: w for w in analytics["win_rates"]}
    assert win_rates["Strong Model"]["win_rate"] == 1.0
    assert win_rates["Weak Model"]["win_rate"] == 0.0

    correctness_avgs = {
        c["model_name"]: c["average_score"]
        for c in analytics["criterion_averages"]
        if c["criterion_name"] == "Correctness"
    }
    assert correctness_avgs["Strong Model"] == 5.0
    assert correctness_avgs["Weak Model"] == 1.0

    failure_counts = {
        (f["model_name"], f["failure_classification"]): f["count"]
        for f in analytics["failure_breakdown"]
    }
    assert failure_counts[("Weak Model", "factual_error")] == 1


def test_evaluation_rejects_rubric_from_another_project(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_a = _create_project(client, headers)
    project_b = _create_project(client, headers)
    rubric_b = _create_rubric(client, headers, project_b)
    task_a_id = _create_task(client, headers, project_a)
    response_id = _add_response(client, headers, task_a_id, "Some Model")

    r = client.post(
        f"{settings.API_V1_STR}/responses/{response_id}/evaluations",
        headers=headers,
        json={"rubric_id": rubric_b["id"], "scores": []},
    )
    assert r.status_code == 400


def test_evaluation_rejects_criterion_from_another_rubric(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)
    rubric = _create_rubric(client, headers, project_id)
    other_rubric = _create_rubric(client, headers, project_id)
    foreign_criterion_id = other_rubric["criteria"][0]["id"]
    task_id = _create_task(client, headers, project_id)
    response_id = _add_response(client, headers, task_id, "Some Model")

    r = client.post(
        f"{settings.API_V1_STR}/responses/{response_id}/evaluations",
        headers=headers,
        json={
            "rubric_id": rubric["id"],
            "scores": [{"criterion_id": foreign_criterion_id, "score": 3}],
        },
    )
    assert r.status_code == 400


def test_update_evaluation_replaces_scores(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)
    rubric = _create_rubric(client, headers, project_id)
    criteria_by_name = {c["name"]: c["id"] for c in rubric["criteria"]}
    task_id = _create_task(client, headers, project_id)
    response_id = _add_response(client, headers, task_id, "Model")

    r = client.post(
        f"{settings.API_V1_STR}/responses/{response_id}/evaluations",
        headers=headers,
        json={
            "rubric_id": rubric["id"],
            "scores": [{"criterion_id": criteria_by_name["Correctness"], "score": 2}],
        },
    )
    evaluation_id = r.json()["id"]

    r = client.put(
        f"{settings.API_V1_STR}/evaluations/{evaluation_id}",
        headers=headers,
        json={
            "justification": "Revised after re-reading the response.",
            "scores": [
                {"criterion_id": criteria_by_name["Correctness"], "score": 4},
                {"criterion_id": criteria_by_name["Safety"], "score": 5},
            ],
        },
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["justification"] == "Revised after re-reading the response."
    assert len(updated["scores"]) == 2


def test_delete_evaluation(client: TestClient, normal_user_token_headers: dict) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)
    rubric = _create_rubric(client, headers, project_id)
    task_id = _create_task(client, headers, project_id)
    response_id = _add_response(client, headers, task_id, "Model")

    r = client.post(
        f"{settings.API_V1_STR}/responses/{response_id}/evaluations",
        headers=headers,
        json={"rubric_id": rubric["id"], "scores": []},
    )
    evaluation_id = r.json()["id"]

    r = client.delete(
        f"{settings.API_V1_STR}/evaluations/{evaluation_id}", headers=headers
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/responses/{response_id}/evaluations", headers=headers
    )
    assert r.json()["count"] == 0
