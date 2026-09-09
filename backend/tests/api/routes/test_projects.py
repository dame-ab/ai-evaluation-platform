from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.project import create_random_project
from tests.utils.user import create_random_user


def test_create_project(client: TestClient, normal_user_token_headers: dict) -> None:
    data = {"name": "Chatbot Eval", "description": "Evaluating our support bot"}
    r = client.post(
        f"{settings.API_V1_STR}/projects/", headers=normal_user_token_headers, json=data
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert content["task_count"] == 0


def test_create_project_requires_auth(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        json={"name": "No auth", "description": None},
    )
    assert r.status_code == 401


def test_read_projects_only_returns_own(
    client: TestClient, db: Session, normal_user_token_headers: dict
) -> None:
    other_user = create_random_user(db)
    create_random_project(db, owner_id=other_user.id)

    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": "Mine", "description": None},
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/projects/", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["data"]]
    assert "Mine" in names
    assert all(name != "Test Project" for name in names)


def test_superuser_sees_all_projects(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    other_user = create_random_user(db)
    project = create_random_project(db, owner_id=other_user.id)

    r = client.get(f"{settings.API_V1_STR}/projects/", headers=superuser_token_headers)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["data"]]
    assert str(project.id) in ids


def test_read_project_not_found(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/projects/00000000-0000-0000-0000-000000000000",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_read_project_forbidden_for_non_owner(
    client: TestClient, db: Session, normal_user_token_headers: dict
) -> None:
    other_user = create_random_user(db)
    project = create_random_project(db, owner_id=other_user.id)

    r = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403


def test_update_and_delete_project(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": "Original", "description": None},
    )
    project_id = r.json()["id"]

    r = client.put(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=normal_user_token_headers,
        json={"name": "Renamed"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    r = client.delete(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_deleting_project_cascades_to_children(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": "Cascade test", "description": None},
    )
    project_id = r.json()["id"]

    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/rubrics",
        headers=normal_user_token_headers,
        json={"name": "Rubric", "description": None, "criteria": []},
    )
    rubric_id = r.json()["id"]

    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/tasks",
        headers=normal_user_token_headers,
        json={"title": "T", "prompt": "P", "reference_answer": None, "category": None},
    )
    task_id = r.json()["id"]

    r = client.delete(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200

    assert (
        client.get(
            f"{settings.API_V1_STR}/rubrics/{rubric_id}",
            headers=normal_user_token_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/tasks/{task_id}", headers=normal_user_token_headers
        ).status_code
        == 404
    )
