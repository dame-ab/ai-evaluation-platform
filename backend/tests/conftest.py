from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    EvalTask,
    Evaluation,
    EvaluationScore,
    ModelResponse,
    Project,
    Rubric,
    RubricCriterion,
    User,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

# Deleted in dependency order so this works the same whether or not the
# database engine enforces foreign keys (SQLite only does with a pragma).
_TABLES_TO_RESET = [
    EvaluationScore,
    Evaluation,
    ModelResponse,
    EvalTask,
    RubricCriterion,
    Rubric,
    Project,
    User,
]


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        yield session
        for table in _TABLES_TO_RESET:
            session.execute(delete(table))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
