## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Database

Create PostgreSQL database:

```sql
CREATE DATABASE smartspend;
```

Run migrations:

```bash
alembic upgrade head
```

## Run

```bash
uvicorn src.app.main:app --reload
```

API docs: http://localhost:8000/api/docs

## API

format:

```json
{
  "data": { ... },
  "error": null,
  "meta": null
}
```

JSON camelCase.

