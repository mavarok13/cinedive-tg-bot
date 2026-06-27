FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY alembic ./alembic
COPY cinedive ./cinedive

RUN pip install --no-cache-dir .

CMD ["python", "-m", "cinedive.app.main"]
