FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps for psycopg (Postgres) building/runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY scripts ./scripts

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "app/main.py"]
