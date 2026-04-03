FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .

RUN pip install --no-cache-dir -e .

EXPOSE 8001

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
