# System Context — Existing FastAPI URL Shortener

## Purpose and evidence boundary

This is reusable context for planning or implementing work in this workspace. It describes only inspected files and observable conventions; it does not assert that Team Collaboration already exists. The repository is a URL shortener. Runtime database connectivity and applied migration state have not been verified. Credential files such as `.env` must not be read or quoted.

## Framework, versions, and project structure

- **Web framework:** FastAPI `0.162.0`, pinned in [`requirements.txt`](../../../requirements.txt) and confirmed installed in the workspace virtual environment.
- **Validation/schema library:** Pydantic `2.14.2` is pinned in `requirements.txt`; request and response schemas are in [`app/schemas.py`](../../../app/schemas.py).
- **ORM/database library:** SQLAlchemy `2.1.6` is pinned in `requirements.txt`. [`app/database.py`](../../../app/database.py) defines a synchronous engine, `sessionmaker`, and shared declarative `Base`. `psycopg2-binary` is pinned; migration syntax also indicates PostgreSQL support/intention, but the live database backend was not verified.
- **Migrations:** Alembic `1.20.1` is pinned. The root [`alembic.ini`](../../../alembic.ini) points to `migrations/`.
- **Tests:** [`tests/test_api.py`](../../../tests/test_api.py) uses pytest-style test functions and FastAPI `TestClient`. `pytest` is not listed in the inspected `requirements.txt`; the active test-runner installation is therefore not guaranteed by that manifest.

Important directories/files:

| Path | Verified role |
|---|---|
| [`app/`](../../../app/) | Application package: `main.py` routes, `database.py` engine/session/base, `schemas.py` Pydantic schemas, and `config.py` settings. |
| [`app/models/`](../../../app/models/) | SQLAlchemy models. [`link.py`](../../../app/models/link.py) currently defines `Link` and `ClickEvent`; [`__init__.py`](../../../app/models/__init__.py) exports them. |
| [`migrations/`](../../../migrations/) | Alembic environment and migration template. |
| [`migrations/versions/`](../../../migrations/versions/) | Schema revisions; the inspected chain creates links/click events and later adds link expiry/tags. |
| [`tests/`](../../../tests/) | API tests, currently in `test_api.py`. |
| [`progress/`](../../) | Existing architecture, trust-audit, and feature-planning documents; documentation is not application implementation. |

No separate `routes/`, `services/`, or authentication package was found in the inspected application tree.

## Route registration and request dependencies

[`app/main.py`](../../../app/main.py) creates one `FastAPI()` instance and registers custom routes directly with decorators such as `@app.get` and `@app.post`. No `APIRouter` or `include_router` pattern was found. FastAPI's default documentation endpoints are framework-provided, not custom business routes.

The route handlers are synchronous `def` functions. Database access is injected with `Depends(get_db)`. [`app/database.py`](../../../app/database.py) implements `get_db()` as a generator that yields a SQLAlchemy session and closes it in `finally`.

No application middleware registration or dedicated dependency-injection container was found. Do not describe a middleware or router-module convention as existing.

## Naming and file conventions observed

- Python module and test filenames use lowercase snake case, for example `app/models/link.py` and `tests/test_api.py`.
- SQLAlchemy model classes use PascalCase (`Link`, `ClickEvent`); tables use lowercase snake case (`links`, `click_events`).
- Models inherit from the shared `Base` and use typed `Mapped[...]` attributes with `mapped_column(...)`.
- Pydantic schema classes use PascalCase names such as `LinkCreate` and `LinkResponse`.
- Alembic revisions use a revision identifier and descriptive filename, declare `revision`/`down_revision`, and implement `upgrade()` and `downgrade()`.
- Tests use `test_*.py` files and `test_*` functions with `TestClient`.

These are observed examples, not proof of a universal convention. Keep additions close to them unless a deliberate, documented refactor is approved.

## Validation and error handling

Verified request validation examples:

- `LinkCreate.long_url` uses Pydantic `HttpUrl`; invalid schemes are rejected by framework validation. `tests/test_api.py::test_reject_javascript_url` expects HTTP 422 and checks for `url_scheme`.
- `GET /links` constrains `skip` with `Query(ge=0)` and `limit` with `Query(ge=1, le=100)` in `app/main.py`; tests check invalid values return HTTP 422.
- `LinkCreate.tags` uses `Field(default_factory=list)`; `expires_at` is an optional `datetime`.

Verified route error examples:

- Missing numeric link ID and missing short code raise `HTTPException` with status 404 and route-specific detail strings in `app/main.py`.
- Expired short links raise `HTTPException` with status 410.
- Successful redirects use `RedirectResponse(status_code=307)`.

**Verified existing FastAPI response shapes:** The installed FastAPI default HTTP exception handler serializes an `HTTPException` with a string detail as `{"detail": "..."}`. For example, the missing-link route raises `HTTPException(status_code=404, detail="Link not found")`, producing `{"detail": "Link not found"}`. FastAPI's default request-validation handler serializes validation failures as `{"detail": [...]}`. These shapes are framework defaults corroborated by the installed FastAPI exception-handler implementation; no custom handler overrides them in `app/main.py`.

No custom global exception handler, unified error envelope, or general status-code policy was found. Preserve the existing FastAPI `detail` response shapes; do not introduce a custom error-response envelope unless explicitly approved. Existing create/list endpoints do not explicitly set a success status code, so a new endpoint's success status should be specified by its own task/contract rather than assumed from a repository-wide convention. Any new server-error response details, especially for authentication configuration failures, are task-specific requirements and must not expose internal exception information.

## Authentication behavior

No authentication or authorization mechanism is present in the inspected application. Current route dependencies provide database sessions only. There is no `User` model, identity provider, token verifier, API-key dependency, or per-user authorization check. Link creation sets `created_by` to the fixed demo label `local-demo`; this is not authenticated identity.

Team Collaboration planning therefore treats identity-provider selection and credential verification as unresolved prerequisites. Never treat a client-supplied user ID, unverified token claim, or arbitrary identity header as authenticated identity.

## Database and migration conventions

- `app/database.py` loads dotenv and requires `DATABASE_URL`; this document does not inspect or reveal any configured value.
- SQLAlchemy uses synchronous sessions. Current models share one declarative `Base`.
- `migrations/env.py` imports `Base` and the model exports, sets `target_metadata = Base.metadata`, and configures online/offline migration execution.
- `alembic.ini` sets `script_location = %(here)s/migrations`; revisions are in `migrations/versions/`.
- The existing revision chain uses `revision` and `down_revision` identifiers and explicit `upgrade()`/`downgrade()` operations. New schema changes require a new migration chained to the actual latest revision, with migration tests against an isolated disposable database.
- PostgreSQL is indicated by the pinned psycopg2 driver and PostgreSQL-style JSON migration syntax. The active URL/backend, connectivity, and applied revision state remain unverified.

## Constraints for future work

1. Do not add a dependency without a specific, reviewed need and approval; prefer existing FastAPI, Pydantic, SQLAlchemy, and standard-library patterns.
2. Never hard-code database credentials, tokens, signing keys, or user identity. Do not read `.env` or other credential files to discover or copy values.
3. Preserve existing route, model, synchronous-session, schema, and migration patterns unless a scoped design explicitly changes them.
4. Include an Alembic migration for every database schema change; inspect the actual current head and keep a single intended revision chain.
5. Test schema/API changes against an isolated disposable database; do not rely on or mutate demo/production records.
6. Do not assume a `User`, authentication, project/task domain, email service, background jobs, or Team Collaboration API exists. Verify before relying on any capability.
7. Keep the product-scope mismatch visible: the inspected application is a URL shortener, while the feature brief refers to a project-management app.
