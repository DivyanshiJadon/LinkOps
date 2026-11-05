# Architecture Summary

## Scope and evidence

This is a static summary of the application and migration structure. `.env` and other credential files were not opened, and no secret values are included. Runtime configuration, database connectivity, and migration state were not inspected or executed; those limits are called out below.

## 1. Folder structure

| Path | Purpose |
|---|---|
| `app/` | FastAPI application package. `main.py` creates the app and defines the HTTP endpoints; `database.py` configures SQLAlchemy and request-scoped sessions; `schemas.py` contains Pydantic request/response schemas; `config.py` defines application settings. |
| `app/models/` | SQLAlchemy ORM model definitions, including links and click events. |
| `migrations/` | Alembic environment and migration template. |
| `migrations/versions/` | Ordered Alembic schema revisions. |
| `tests/` | API tests using FastAPI's `TestClient`. |
| `scripts/` | Helper scripts; `module-02-seed-query.py` writes and reads a demo link. |
| `progress/evidence/` | Saved evidence files, including module-02 query/index evidence. |
| `progress/ai-augmented-engineering/module-01/` | Evidence/work area for the AI-Augmented Engineering module. |
| `.github/` | Repository-specific GitHub/Copilot instructions. |
| `.venv/` | Python virtual environment; its contents were not inspected. |
| `.pytest_cache/` | Generated pytest cache, not application code. |

Important root-level project files include `requirements.txt` for Python dependencies and `alembic.ini` as the Alembic configuration entry point.

## 2. Data models

The ORM models inherit from the shared SQLAlchemy declarative `Base` in `app/database.py`; both are defined in `app/models/link.py`.

### `Link` (`links`)

| Field | Type / constraints | Purpose or notes |
|---|---|---|
| `id` | Integer primary key | Database identity. |
| `code` | String(50), unique and indexed | Short code used for lookup and redirects. |
| `long_url` | String(2048), non-null | Destination URL. |
| `created_at` | Timezone-aware datetime | Defaults to the current UTC time. |
| `expires_at` | Nullable timezone-aware datetime | Optional expiry checked by the redirect endpoint. |
| `tags` | Non-null JSON, default empty list | Tags associated with the link; the API schema types these as strings. |
| `created_by` | String(100), non-null and indexed | The current create endpoint assigns the fixed value `local-demo`. |

### `ClickEvent` (`click_events`)

| Field | Type / constraints | Purpose or notes |
|---|---|---|
| `id` | Integer primary key | Database identity. |
| `link_id` | Integer, non-null foreign key to `links.id` | Database-level association to a link. |
| `clicked_at` | Timezone-aware datetime | Defaults to the current UTC time. |
| `user_agent` | Nullable String(500) | Optional request metadata. |
| `referrer` | Nullable String(2048) | Optional request metadata. |
| `ip_hash` | Nullable String(128) | Field for a hashed IP value; hashing behavior is not established by the model itself. |

`click_events` has a composite index on `(link_id, clicked_at)`. The foreign key links each click event to a link, but no SQLAlchemy ORM `relationship()` property is defined. The inspected routes do not create or query `ClickEvent` records.

The Pydantic schemas in `app/schemas.py` are distinct from the ORM models:

- `LinkCreate` accepts `long_url` as an `HttpUrl`, optional `expires_at`, and `tags` defaulting to an empty list.
- `LinkResponse` includes `id`, `code`, `short_url`, `long_url`, and `created_at`; it does not expose expiry, tags, or creator.

## 3. API routes

Five application routes are declared directly on the FastAPI app in `app/main.py`; no separate router/prefix setup was found.

| Method | Path | Purpose and observed behavior |
|---|---|---|
| `GET` | `/health` | Health check returning `{"ok": true}`. |
| `POST` | `/links` | Creates a link from a `LinkCreate` body, generates a URL-safe code, persists the link, and returns `LinkResponse`. The creator is hard-coded as `local-demo`. |
| `GET` | `/links` | Lists links in ID order. `skip` defaults to 0 and must be nonnegative; `limit` defaults to 10 and is constrained to 1–100. |
| `GET` | `/links/{link_id}` | Retrieves a link by integer database ID; returns 404 if it does not exist. |
| `GET` | `/r/{code}` | Looks up a short code and redirects to its destination with HTTP 307. Returns 404 for an unknown code and 410 for an expired link. |

Because the app is created with FastAPI's default documentation configuration, the framework also provides these generated routes:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/openapi.json` | OpenAPI schema. |
| `GET` | `/docs` | Swagger UI. |
| `GET` | `/docs/oauth2-redirect` | OAuth redirect helper used by Swagger UI. |
| `GET` | `/redoc` | ReDoc API documentation. |

These are framework-generated documentation routes, not custom business endpoints.

## 4. Authentication and authorization

No authentication or authorization mechanism was found in the application routes. The route dependencies are database-session dependencies; no identity provider, token, API key, or user authorization dependency is evidenced. Link creation sets `created_by` to the fixed value `local-demo`, rather than deriving it from an authenticated identity. Per-user access controls are not evidenced.

## 5. Database and migrations

- **ORM and sessions:** SQLAlchemy synchronous engine and `sessionmaker`. `get_db()` yields a session and closes it in a `finally` block.
- **Connection configuration:** `app/database.py` loads dotenv and requires `DATABASE_URL` from the process environment. `migrations/env.py` loads dotenv and uses the same variable to configure Alembic. No value from `.env` or any credential file was inspected or reproduced.
- **Database technology:** `requirements.txt` includes SQLAlchemy, Alembic, and `psycopg2-binary`; a migration uses PostgreSQL-style JSON server-default syntax. These indicate PostgreSQL is intended or supported, but do not establish which backend is currently configured or deployed.
- **Migrations:** Alembic is configured from the root `alembic.ini`. `migrations/env.py` imports model metadata and supports offline and online migration execution. The visible revision chain is:
  1. `033349e24f31_create_links_and_click_events.py` creates `links` and `click_events`, including their indexes and foreign key.
  2. `21fb1444a3f8_add_expiry_and_tags_to_links.py` adds `expires_at` and JSON `tags` to `links`.
- **Other settings:** `app/config.py` defines a Pydantic `Settings` class with a `port` setting and an `.env` source. The inspected application/database code does not use this settings object, so whether it affects runtime launch behavior is unverified.

## Not verified

The active database URL/backend, connectivity, deployment configuration, and which migrations have actually been applied cannot be verified from this static review. Tests and runtime behavior were not executed.
