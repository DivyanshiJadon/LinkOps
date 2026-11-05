# Context Bundles — TC-01, TC-02, and TC-03

## Reading guide

The bundles below are derived from the task definitions and full prompts in [`module-02/task-tree.md`](../module-02/task-tree.md), the system evidence in [`system-context.md`](./system-context.md), and current source inspection. The repository currently has no Team Collaboration implementation. Paths marked **planned output** are not existing files unless explicitly noted.

All three tasks are blocked on the task tree's product-scope and/or identity prerequisites as indicated below. No implementation prompt was executed in preparing these bundles.

### Verified error convention versus task-specific requirements

- **Verified existing convention:** FastAPI `HTTPException` responses use `{"detail": "..."}` for string details; request-validation errors use `{"detail": [...]}`. The application has no custom error handler or unified error envelope.
- **Constraint for any API/auth task below:** Preserve these existing FastAPI response shapes. Do not invent a different error-response structure or add a custom envelope unless explicitly approved.
- **Task-specific requirement, not existing behavior:** TC-02 requires safe handling of identity-provider/verifier configuration failures. The project has no existing authentication error behavior; TC-02 must use the existing `HTTPException`/FastAPI handling mechanism and generic safe detail, without exposing secrets, credentials, bearer tokens, or internal exception details.

---

## TC-01 — Persist verified external user identities

### Task name and scope

**Name:** Persist verified external user identities.

**Scope and purpose (task-tree wording):** “Add the smallest local identity record needed to associate team membership with a principal authenticated by the approved provider. Store an internal ID, issuer, subject, and creation timestamp; enforce uniqueness of `(issuer, subject)`. Do not create a login system.”

### System-level context

Read [`system-context.md`](./system-context.md), especially its ORM/model, migration, test, database-safety, and missing-authentication sections. The current model style is synchronous SQLAlchemy with a shared declarative `Base`; no User model or identity provider exists.

### Files to read

| File/path | Status | Why read it | Risk if omitted |
|---|---|---|---|
| [`app/database.py`](../../../app/database.py) | Existing | Use the actual `Base` and understand session/database configuration. | A model could inherit from the wrong base or tests/migrations could target an unsafe database. |
| [`app/models/link.py`](../../../app/models/link.py) | Existing | Match typed `Mapped`/`mapped_column` conventions. | Model style/types could diverge from current code. |
| [`app/models/__init__.py`](../../../app/models/__init__.py) | Existing | Understand current exports and how Alembic imports models. | The new model may be missing from metadata registration or exports. |
| [`migrations/env.py`](../../../migrations/env.py) | Existing | Verify the actual metadata import and migration modes. | Alembic autogeneration may omit the new table. |
| [`migrations/versions/`](../../../migrations/versions/) | Existing directory and two revisions | Inspect all revision IDs and the actual current head before choosing `down_revision`. | A revision may fork the chain or use an incorrect parent. |
| [`tests/test_api.py`](../../../tests/test_api.py) | Existing | Learn current pytest/FastAPI test conventions and see that tests are not shown to provide an isolated DB fixture. | New model tests could accidentally depend on demo rows or a live configured database. |
| [`requirements.txt`](../../../requirements.txt) | Existing | Verify dependencies; the current manifest includes SQLAlchemy/Alembic and does not provide an identity system. | The implementation might assume an uninstalled provider/auth library. |
| [`alembic.ini`](../../../alembic.ini) | Existing | Verify Alembic script location and project configuration without exposing connection values. | Revision files could be placed or invoked using an invented migration layout. |
| Approved identity-contract decision | **Missing external prerequisite; no existing file identified** | Establish trusted issuer/subject semantics and who verifies them. | A local user record could be based on an untrusted or ambiguous identity. |

### Files to modify or create

- **Planned new output:** `app/models/user.py`
- **Modify existing:** `app/models/__init__.py`
- **Planned new output:** one Alembic revision in `migrations/versions/`
- **Planned new output:** `tests/test_user_model.py`
- No API route changes or auth implementation are specified for this task.

### Expected outputs and external acceptance criteria

As specified in the task tree:

- The user table has an internal integer ID, issuer, subject, creation timestamp, and unique `(issuer, subject)` constraint.
- Alembic sees the model through the existing metadata import.
- On an isolated database, migration upgrade creates the table and uniqueness constraint; duplicate pairs are rejected; distinct pairs can persist/query; downgrade removes the new table cleanly.
- Tests use an explicitly isolated disposable database, not demo or production data.
- Maximum change budget: **130 changed lines** across deliverables.

### Dependencies, assumptions, and unresolved prerequisites

- **Dependencies:** Product scope and identity gates must be resolved; use the existing shared `Base` and actual current Alembic head.
- **Assumption/proposed design:** The stable pair `(issuer, subject)` is the provider's verified identity key; do not add email/password/login fields unless separately approved.
- **Missing prerequisites:** Product owner confirmation that this repo is in scope; approved identity provider and verification contract; disposable isolated PostgreSQL test DB and safe migration target.
- The task must stop without changes if the identity contract is absent or ambiguous.

---

## TC-02 — Resolve requests to an authenticated user

### Task name and scope

**Name:** Resolve requests to an authenticated user.

**Scope and purpose (task-tree wording):** “Integrate the approved verifier and expose a fail-closed FastAPI dependency that validates the incoming credential and resolves/upserts the corresponding local user. Invalid, missing, expired, wrong-issuer, or wrong-audience credentials must not become an authenticated principal.”

### System-level context

Read [`system-context.md`](./system-context.md), especially route dependency injection and the explicit absence of current authentication. Existing route handlers use synchronous FastAPI `Depends(get_db)`; do not assume there is an auth middleware or framework already installed.

### Files to read

| File/path | Status | Why read it | Risk if omitted |
|---|---|---|---|
| [`app/main.py`](../../../app/main.py) | Existing | Inspect the actual `FastAPI` instance and route dependency usage. | Auth integration may introduce a nonexistent router/middleware convention or affect unrelated routes. |
| [`app/database.py`](../../../app/database.py) | Existing | Understand `get_db`, `SessionLocal`, and shared `Base`; never expose the URL value. | User lookup/upsert may use the wrong session lifecycle or unsafe configuration assumptions. |
| [`app/models/user.py`](../../../app/models/user.py) | **Planned output of TC-01; currently absent** | Consume the exact User fields and unique issuer/subject constraint produced by TC-01. | Auth code could assume a schema that TC-01 did not create. |
| [`app/models/__init__.py`](../../../app/models/__init__.py) | Existing now; expected to be modified by TC-01 | Verify the actual User export after TC-01. | Imports may fail or use an unregistered model. |
| `app/auth.py` | **Planned output of TC-02; currently absent** | The task-tree full prompt says to confirm absence if not created by earlier partial work; it is the expected output, not a pre-existing input. | Treating it as an existing interface could lead to fabricated imports. |
| [`requirements.txt`](../../../requirements.txt) | Existing | Check installed/pinned packages before choosing an approved verifier. | An implementation could assume JWT/auth tooling that is not present or add dependencies without approval. |
| [`tests/test_api.py`](../../../tests/test_api.py) | Existing | Match TestClient/pytest conventions and identify current database coupling. | Tests could be coupled to current demo data or omit relevant request behavior. |
| `tests/test_user_model.py` | **Planned output of TC-01; currently absent** | The full TC-02 prompt asks to inspect it if TC-01 creates it; use it for the model's isolated test setup. | Test assumptions may not match the delivered TC-01 fixtures. |
| Approved provider/verifier and deployment contract | **Missing external prerequisite; no existing file identified** | Specify issuer, audience, signature/key discovery/rotation, credential transport, and trusted runtime configuration. | A verifier could accept forged identities or be unusable in deployment. |
| TC-01 implementation results | **Future handoff, not an existing file** | Confirm what was actually implemented rather than trusting a planned interface. | User lookup/upsert may mismatch model fields, constraints, or migration state. |

### Files to modify or create

- **Planned new output:** `app/auth.py`
- **Planned new output:** `tests/test_auth.py`
- **Conditional modification:** `requirements.txt` only if a reviewed provider integration truly needs an additional maintained verifier and the dependency is explicitly approved.
- Do not add login/signup endpoints, protect unrelated routes, or change Link behavior in this task.
- **Verified existing convention:** For HTTP errors, use FastAPI's existing `HTTPException` mechanism and its default `{"detail": ...}` response shape; for request-validation errors, preserve `{"detail": [...]}`. Do not create a new error envelope.

### Expected outputs and external acceptance criteria

As specified in the task tree and full prompt:

- A typed authenticated-principal dependency verifies credentials according to the approved provider contract and resolves the local User by verified issuer/subject.
- Valid credentials resolve the expected persisted User. Missing, invalid, expired, wrong-issuer, or wrong-audience credentials return 401 and never resolve a User.
- **New TC-02 requirement (not existing project behavior):** Verifier or identity-provider configuration failures fail closed and return a safe server error using the existing `HTTPException`/FastAPI error-handling mechanism. Use a generic `detail` message; do not expose secrets, credentials, tokens, or internal exception details.
- No caller-supplied user IDs or unverified headers are trusted. No bearer token is logged.
- Tests use isolated data; provider-supported test keys/fixtures are used when available. Do not add an unapproved dependency.
- Maximum change budget: **140 changed lines**; split verifier setup from local-user resolution if needed.

### Dependencies, assumptions, and unresolved prerequisites

- **Dependencies:** `TC-01`; approved provider/verifier and deployment configuration contract. The task is explicitly blocked until identity is resolved.
- **Task handoff clarification:** Bind the implementation to the exact `User` fields and `(issuer, subject)` uniqueness constraint that TC-01 actually creates. Do not introduce any team or membership schema in TC-02.
- **Missing prerequisites:** Provider/verifier choice, trusted credential delivery/runtime configuration, issuer/audience/key-rotation contract, test-verification strategy, and approved dependency decision if needed.
- If no trustworthy provider contract exists, stop; do not build custom cryptography, a static identity, or a mock-only production path.

---

## TC-03 — Add the team entity

### Task name and scope

**Name:** Add the team entity.

**Scope and purpose (task-tree wording):** “Define a minimal team table with generated ID, bounded non-empty name, and creation timestamp. Do not add guessed project/link ownership fields.”

### System-level context

Read [`system-context.md`](./system-context.md), especially the model and migration sections. The repository currently has Link and ClickEvent models, not Project, Task, Team, or User models. Routes are out of scope for TC-03.

### Files to read

| File/path | Status | Why read it | Risk if omitted |
|---|---|---|---|
| [`app/database.py`](../../../app/database.py) | Existing | Use the shared `Base`; understand the synchronous DB configuration without reading secrets. | Model registration or safe DB-test setup may be wrong. |
| [`app/models/link.py`](../../../app/models/link.py) | Existing | Follow actual model field/type/timestamp style. | Team model may introduce inconsistent SQLAlchemy conventions. |
| [`app/models/user.py`](../../../app/models/user.py) | **Planned output of TC-01; currently absent** | Verify prior user model handoff as required by the task; do not invent columns or relationships. | The plan may not match the model actually delivered by TC-01. |
| [`app/models/__init__.py`](../../../app/models/__init__.py) | Existing now; expected to be modified by earlier model tasks | Verify current exports and add Team without losing existing exports. | Alembic may not load the new model or may drop prior exports. |
| [`migrations/env.py`](../../../migrations/env.py) | Existing | Confirm `Base.metadata` and import behavior. | New Team model might not be represented in migration metadata. |
| [`migrations/versions/`](../../../migrations/versions/) | Existing directory and current revisions | Determine actual head and preserve a single linear revision chain. | Migration could fork or have an invalid `down_revision`. |
| [`tests/test_api.py`](../../../tests/test_api.py) | Existing | Inspect current test conventions and known DB coupling. | Tests could repeat demo-data assumptions or use a wrong fixture pattern. |
| `tests/test_user_model.py` | **Planned output of TC-01; currently absent** | The full TC-03 prompt names this as a possible test/database convention to inspect after TC-01. | Test isolation assumptions could be missed. |
| Product scope confirmation | **Missing external prerequisite; no existing file identified** | Verify that adding a generic team entity belongs in this URL-shortener repository and clarify what teams collaborate around. | Team schema may solve the wrong product problem. |
| TC-01/TC-02 implementation results | **Future handoff, not an existing file** | Verify actual outputs before depending on them. | Planned user/auth contracts may not match implementation. |

### Files to modify or create

- **Planned new output:** `app/models/team.py`
- **Modify existing:** `app/models/__init__.py`
- **Planned new output:** one linear Alembic revision in `migrations/versions/`
- **Planned new output:** `tests/test_team_model.py`
- No route or API-schema file changes are specified for this task.

### Expected outputs and external acceptance criteria

As specified in the task tree and full prompt:

- The Team table has a generated integer ID, bounded non-empty name, and creation timestamp; no guessed project/link ownership fields.
- The Team model is exported so Alembic's existing model import path makes it visible to `Base.metadata`.
- One revision is chained to the actual latest revision and implements upgrade/downgrade.
- On an isolated disposable PostgreSQL test database, upgrade creates the table, downgrade removes it, valid names persist, invalid/empty names are rejected at the agreed validation boundary, and safe rollback is verified.
- Existing Link and ClickEvent definitions and behavior are unchanged.
- Maximum change budget: **120 changed lines**.

### Dependencies, assumptions, and unresolved prerequisites

- **Dependencies:** `TC-01`, `TC-02`, and the product-scope gate; verify the current actual Alembic head.
- **Assumptions:** The minimal Team entity is useful without a project/task relation. Team ownership/membership is intentionally not an `owner_id` column in TC-03; membership and roles are introduced later by TC-04.
- **Missing prerequisites:** Product owner confirmation; successful prior user/auth tasks and their actual outputs; safe isolated PostgreSQL DB and migration target.
- If scope or migration head is unclear, stop and report rather than guessing.

## Review checklist: bundle consistency

- The bundle scopes and task dependencies match `TC-01`, `TC-02`, and `TC-03` in the task tree.
- Current files and planned outputs are labeled separately; notably `app/models/user.py`, `app/auth.py`, `tests/test_user_model.py`, and `tests/test_team_model.py` do **not** currently exist.
- The bundles preserve the actual URL-shortener baseline and do not claim existing Team Collaboration, project/task models, authentication, or an identity provider.
- No implementation, schema migration, test, or configuration work is requested by these context bundles.
