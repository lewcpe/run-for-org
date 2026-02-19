# Run for Organization Backend

Backend service for the "Run for Organization" virtual run event. Built with FastAPI, SQLAlchemy, and SQLite.

## Features

- **User Management**: Authentication via Auth0/Firebase (JWT), user profile management (firstname, lastname).
- **Activity Tracking**: Log running activities with automatic step/distance conversion.
- **Statistics**: Organization-wide progress tracking, weekly stats, and leaderboards.
- **Audit Logging**: Track important actions for compliance and debugging.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (dev) with SQLAlchemy ORM
- **Migrations**: Alembic
- **Dependency Management**: uv
- **Testing**: pytest

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd run-for-org
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure Environment:
   Create a `.env` file (or set environment variables) with the following configurations:
   ```env
   DATABASE_URL=sqlite:///./sql_app.db
   SECRET_KEY=your-secret-key
   RUNORG_START_DATE=2023-01-01
   RUNORG_END_DATE=2023-12-31
   RUNORG_TOTAL_STEP_GOAL=1000000
   RUNORG_STEP_PER_KM=1500
   ```

4. Run Database Migrations:
   ```bash
   uv run alembic upgrade head
   ```

### Running the Application

Start the development server:
```bash
uv run uvicorn backend.main:app --reload
```

The API will be available at http://127.0.0.1:8000.
Interactive API documentation is available at http://127.0.0.1:8000/docs.

## Testing

Run the test suite using pytest:
```bash
uv run python -m pytest backend/tests/test_api.py
```

## API Overview

- **`GET /api/config`**: Get public configuration (start date, end date, goals).
- **`GET /api/me`**: Get current user's profile and aggregated statistics.
- **`PUT /api/me`**: Update user profile (firstname, lastname).
- **`GET /api/me/logs`**: List running logs.
- **`POST /api/me/logs`**: Create a new running log (steps or distance).
- **`PUT /api/me/logs/{id}`**: Update a running log.
- **`DELETE /api/me/logs/{id}`**: Delete a running log.
- **`GET /api/stats/progress`**: Get organization-wide progress towards the goal.
- **`GET /api/stats/leaderboard`**: Get the top runners leaderboard.
- **`GET /api/stats/weekly`**: Get weekly statistics.

## Project Structure

```
.
├── alembic/                # Database migrations
├── backend/
│   ├── routers/            # API endpoints
│   ├── tests/              # Test suite
│   ├── auth.py             # Authentication logic
│   ├── config.py           # Application configuration
│   ├── crud.py             # Database CRUD operations
│   ├── database.py         # Database connection setup
│   ├── main.py             # App entrypoint
│   ├── models.py           # SQLAlchemy models
│   └── schemas.py          # Pydantic data models
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # Project documentation
```
