from fastapi.testclient import TestClient

from app.core.config import settings


def _create_project(client: TestClient, headers: dict) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=headers,
        json={"name": "Rubric Test Project", "description": None},
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_create_rubric_with_criteria(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)

    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/rubrics",
        headers=headers,
        json={
            "name": "Support Quality Rubric",
            "description": "Five-dimension rubric",
            "criteria": [
                {"name": "Correctness", "weight": 1.5, "max_score": 5, "order": 0},
                {"name": "Clarity", "weight": 1.0, "max_score": 5, "order": 1},
            ],
        },
    )
    assert r.status_code == 200
    rubric = r.json()
    assert rubric["name"] == "Support Quality Rubric"
    assert len(rubric["criteria"]) == 2

    r = client.get(
        f"{settings.API_V1_STR}/projects/{project_id}/rubrics", headers=headers
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1


def test_add_update_delete_criterion(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    headers = normal_user_token_headers
    project_id = _create_project(client, headers)
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/rubrics",
        headers=headers,
        json={"name": "Rubric", "description": None, "criteria": []},
    )
    rubric_id = r.json()["id"]

    r = client.post(
        f"{settings.API_V1_STR}/rubrics/{rubric_id}/criteria",
        headers=headers,
        json={"name": "Completeness", "weight": 1.0, "max_score": 5, "order": 0},
    )
    assert r.status_code == 200
    criterion_id = r.json()["id"]

    r = client.put(
        f"{settings.API_V1_STR}/rubrics/{rubric_id}/criteria/{criterion_id}",
        headers=headers,
        json={"weight": 2.0},
    )
    assert r.status_code == 200
    assert r.json()["weight"] == 2.0

    r = client.delete(
        f"{settings.API_V1_STR}/rubrics/{rubric_id}/criteria/{criterion_id}",
        headers=headers,
    )
    assert r.status_code == 200

    r = client.get(f"{settings.API_V1_STR}/rubrics/{rubric_id}", headers=headers)
    assert r.json()["criteria"] == []


def test_rubric_not_found(client: TestClient, normal_user_token_headers: dict) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/rubrics/00000000-0000-0000-0000-000000000000",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
