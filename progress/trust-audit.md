# Extension Points: Trust Audit

## Scope and evidence

This report answers where future features fit based on the existing FastAPI project. The statements below distinguish inspected project behavior from recommendations. `.env` and credential files were not read, and this analysis did not modify application source code.

## 1. Adding API routes

**Verified existing pattern:** The application is created and its five custom routes are defined directly on the FastAPI instance in [`app/main.py`](../app/main.py#L11). Route handlers use `@app.get` and `@app.post` decorators. No `APIRouter` or `include_router` pattern was found in the application code.

**Recommendation:** A small route addition can follow the existing pattern in `app/main.py`. Organizing routes into separate router modules is a possible future refactor, but it is not an established convention in this codebase.

## 2. Adding database models

**Verified existing pattern:** SQLAlchemy models are defined in [`app/models/link.py`](../app/models/link.py#L13), inherit from the shared `Base`, and use typed `Mapped` fields with `mapped_column`. The file currently contains both `Link` and `ClickEvent`; there is not a one-model-per-file pattern. Model exports are gathered in [`app/models/__init__.py`](../app/models/__init__.py#L1).

Alembic imports `Base` and the model exports in [`migrations/env.py`](../migrations/env.py#L24) and uses `Base.metadata` as its target metadata. Revisions are stored in [`migrations/versions/`](../migrations/versions/); the current visible chain starts with [`033349e24f31_create_links_and_click_events.py`](../migrations/versions/033349e24f31_create_links_and_click_events.py#L15) and continues with [`21fb1444a3f8_add_expiry_and_tags_to_links.py`](../migrations/versions/21fb1444a3f8_add_expiry_and_tags_to_links.py#L15). Revisions provide `upgrade()` and `downgrade()` functions.

**Recommendation:** Define a new model using the existing declarative `Base` and typed-column style. Export it from `app/models/__init__.py` and ensure it is imported by Alembic's environment so its table is included in `Base.metadata`. Add schema changes as a new Alembic revision in `migrations/versions/`, with upgrade and downgrade operations chained to the current revision. These steps follow the observed metadata and revision setup; automated migration generation or application was not run as part of this review.

## 3. Middleware and dependency injection

**Verified existing pattern:** The routes use FastAPI dependency injection for database access, for example `Depends(get_db)` in [`app/main.py`](../app/main.py#L19). The `get_db()` dependency in [`app/database.py`](../app/database.py#L23) yields a SQLAlchemy session and closes it in a `finally` block. No application middleware registration or dedicated dependency-injection container was found in the inspected application code.

**Recommendation:** A dependency that supplies a resource to selected routes can follow the `get_db()` / `Depends(...)` pattern. Middleware would be a new pattern here rather than an extension of existing middleware code.

## 4. Background jobs and asynchronous work

**Verified existing pattern:** No project-level background-task system, queue, worker, or scheduler was found. The route handlers in [`app/main.py`](../app/main.py#L15) are synchronous `def` functions; no `async def` route or use of FastAPI `BackgroundTasks` was found in the application code.

**Recommendation:** There is no existing background-job or async-work convention to extend. Choosing one for future work would require a separate design decision; this review does not assume a queue, worker, or async architecture.

## Trust assessment

- **Trust:** The route-file location, model declarations/exports, Alembic metadata imports, and session dependency behavior are directly evidenced by the referenced project files.
- **Trust with scope limit:** Statements that a middleware, router, or background-job pattern was not found apply to the inspected application code; they do not prove that no external deployment component or uninspected infrastructure provides one.
- **Recommendation, not current behavior:** Any suggestion to keep routes in `main.py`, add a separate router structure, register a new model, or select a future job-processing approach describes a possible next step, not functionality already implemented.

## Module 01 BREAK — Wrong-Claim Verification

### Claim said

> "This starter workspace is only a platform folder with AGENTS.md, CLAUDE.md, reports, and progress/; it has no real application files to test."

### Verification commands

1. `ls`
2. `find . -maxdepth 3 -type f | sort | grep -E '(src|packages|routes|models|services|tests|package.json)'`
3. `python -m pytest -q`

### Observed

- The workspace root contains `app/`, `migrations/`, `tests/`, `requirements.txt`, and `alembic.ini`, in addition to management and report files.
- The file search found `app/models/__init__.py`, `app/models/link.py`, and `tests/test_api.py`.
- The test suite reported 7 passed and 3 failed. The failures were `test_get_existing_link`, `test_redirect_existing_link`, and `test_redirect_expired_link`; each received HTTP 404 instead of its expected response.
- One Starlette deprecation warning was reported.

### Corrected

> "The workspace contains a real Python FastAPI application, SQLAlchemy model files, Alembic migrations, and API tests. It is not merely a platform folder. The current test suite runs, with 7 tests passing and 3 failing because expected demo-link responses returned 404."

## Module 01 FIX — Corrected Claim

### Original claim

> "This starter workspace is only a platform folder with AGENTS.md, CLAUDE.md, reports, and progress/; it has no real application files to test."

### Corrected statement

> The workspace contains a real Python FastAPI application, SQLAlchemy database models, Alembic migrations, and API tests. The management and report files are present alongside that application; they do not make the workspace a platform-only folder.

### Evidence from this workspace

- The root contains `app/`, `migrations/`, `tests/`, `requirements.txt`, and `alembic.ini`. This was confirmed by listing those paths; the root also contains management/report material.
- [`app/main.py`](../app/main.py#L1) imports FastAPI, constructs `app = FastAPI()` at line 11, and defines routes including `GET /health` at lines 14–16 and `POST /links` at lines 19–44. This is application code, not just workspace metadata.
- [`app/models/link.py`](../app/models/link.py#L13) imports the shared SQLAlchemy `Base` and declares the `Link` model at lines 16–41 and `ClickEvent` at lines 44–62. [`app/models/__init__.py`](../app/models/__init__.py#L1) exports both.
- [`tests/test_api.py`](../tests/test_api.py#L1) imports FastAPI's `TestClient` and the application at lines 1–5, then defines API tests, including the health check at lines 8–12.
- [`migrations/env.py`](../migrations/env.py#L6) imports Alembic's migration context and sets model metadata at lines 24–35. Actual revisions exist in [`migrations/versions/`](../migrations/versions/), including [`033349e24f31_create_links_and_click_events.py`](../migrations/versions/033349e24f31_create_links_and_click_events.py#L15) and [`21fb1444a3f8_add_expiry_and_tags_to_links.py`](../migrations/versions/21fb1444a3f8_add_expiry_and_tags_to_links.py#L15).
- [`requirements.txt`](../requirements.txt#L1) lists Alembic, FastAPI, SQLAlchemy, and other Python dependencies. [`alembic.ini`](../alembic.ini#L8) configures Alembic's script location as `migrations`.

### Corrected prompting approach

Ask for an inventory of the actual workspace before characterizing it: inspect the root and the named application, model, test, migration, and configuration paths; cite the files that establish whether application code exists; and distinguish observed contents from assumptions about a starter template. If any paths cannot be inspected, state that limitation instead of concluding the workspace has no application.

### Likely error cause

The evidence makes insufficient context or a failure to inspect/use the workspace inventory the best-supported explanation: the relevant application and test files exist, and their roles are explicit in their contents. Ambiguous code is not supported by this evidence. However, the files cannot establish how the original claim was produced, so it is not possible to determine conclusively whether the underlying failure should specifically be called a hallucination rather than an inspection/context failure.
