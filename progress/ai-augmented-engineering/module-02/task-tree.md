# Team Collaboration — Implementation Task Tree

## 1. Purpose, verified baseline, and scope gate

This is a plan only. No application code, migration, test, database record, or configuration was changed to produce it.

### Verified facts from this workspace

- The existing application is a **FastAPI URL shortener**, not a project-management application. [`app/main.py`](../../../app/main.py) defines health, link creation/list/retrieval, and short-code redirect endpoints. No project/task domain model or route was found.
- Custom endpoints are defined directly on the single FastAPI application in [`app/main.py`](../../../app/main.py); no `APIRouter` structure was found.
- SQLAlchemy uses a shared declarative `Base` and synchronous request sessions from [`app/database.py`](../../../app/database.py). Existing models are `Link` and `ClickEvent` in [`app/models/link.py`](../../../app/models/link.py), exported by [`app/models/__init__.py`](../../../app/models/__init__.py).
- Request/response schemas are in [`app/schemas.py`](../../../app/schemas.py). API tests use FastAPI `TestClient` in [`tests/test_api.py`](../../../tests/test_api.py).
- Alembic reads model metadata in [`migrations/env.py`](../../../migrations/env.py), and revisions are in [`migrations/versions/`](../../../migrations/versions/). [`alembic.ini`](../../../alembic.ini) points to the `migrations` directory. [`requirements.txt`](../../../requirements.txt) includes FastAPI, SQLAlchemy, Alembic, and `psycopg2-binary`; it does not list a JWT/authentication, email, queue, or background-job package.
- The inspected application contains no `User` model, authentication/authorization dependency, email service, middleware registration, or background-job framework. Link creation currently writes the literal `local-demo` into `created_by`; that is not an authenticated user identity.
- The prior architecture summary notes PostgreSQL is intended/supported based on dependencies and migration syntax, but the active database URL/backend and applied revision state were not verified. Do not inspect or print credential values to resolve those questions.
- The existing API tests are not shown to create an isolated database fixture. The earlier trust audit records a run with 7 passing and 3 failing tests, where three demo-link expectations returned 404. Treat that as recorded baseline evidence, not proof of the current test state.

### Explicit scope and prerequisite gates

1. **Product scope gate:** “Add team collaboration to the project management app” does not match the inspected URL-shortener domain, and no `Project` model exists. Before implementation, the product owner must confirm whether this feature belongs in this repository and what resource teams collaborate around. The sequence below proposes a minimal generic team/membership foundation only; it deliberately does not transfer link ownership or invent project/task entities.
2. **Identity gate:** No authentication system exists. Before Task `TC-01`, select and document a trusted identity provider or trusted host integration, its token-verification contract, issuer, stable subject claim, local development/test approach, and ownership of key rotation. Do not accept client-supplied user IDs, unverified identity headers, decoded-but-unverified JWTs, or a hard-coded demo identity. If no approved verifier is available in the existing dependencies, pause and request approval for a maintained verification dependency; do not implement custom cryptography.
3. **Invitation-delivery decision:** No email service exists. The proposed first release issues a high-entropy bearer invitation token and returns it exactly once to an authorized inviter for out-of-band delivery. Anyone possessing it can redeem it, so users must be warned to share it securely. If product policy requires recipient-bound invitations or email delivery, stop and decide the verified recipient identity and email-delivery integration before `TC-09`; do not pretend those facilities already exist.
4. **Database/test gate:** Confirm a disposable, isolated PostgreSQL test database and a safe migration target before applying schema changes. Never point migration or test commands at an unknown or production database. Do not read `.env` contents to discover credentials.

### Proposed decisions (not existing behavior)

- Use internal integer `User.id` values, mapped uniquely to the trusted `(issuer, subject)` pair from verified authentication.
- Protect all team and invitation routes with the authenticated-user dependency. A team is visible only to its members.
- Roles are `owner`, `admin`, and `member`. The initial owner is created as a membership in the same transaction as the team. Ownership transfer is out of the initial scope and requires a separately specified atomic operation.
- Invitations are bearer secrets generated with a cryptographically secure random source; persist only a SHA-256 digest, apply a bounded expiry, support revocation, and allow exactly one successful redemption.
- Record security-relevant team mutations in an append-only activity table in the same database transaction as each mutation. Never put invitation secrets, credentials, or raw authentication tokens in audit metadata or logs.
- Continue the existing synchronous SQLAlchemy/FastAPI style and Pydantic schemas. Do not add a framework or dependency unless a reviewed auth-provider integration demonstrably requires one.

## 2. Task rules and sequencing

- Every implementation task below has a maximum budget of **150 changed lines total** across its deliverables (including tests and migrations). Treat this as a hard cap, not a target. If the task cannot meet it, stop and split it into smaller tasks before editing.
- Each task must inspect its named files at execution time; do not assume files or interfaces have remained unchanged. Later work should be refined against the actual result of earlier tasks.
- Add focused tests in the existing pytest/FastAPI style. Tests must use an explicitly isolated disposable database and must not depend on existing demo rows or mutate an unknown database. Test Alembic upgrades/downgrades against that isolated database.
- Keep each Alembic revision on one linear chain: inspect the latest actual revision before creating each migration; do not create competing heads.
- Preserve existing routes and behavior. Because there is no router-module convention, the initial implementation should add routes to `app/main.py` unless the product owner explicitly approves a separate-router refactor.

## 3. Atomic implementation tasks

### TC-01 — Persist verified external user identities

- **Scope and purpose:** Add the smallest local identity record needed to associate team membership with a principal authenticated by the approved provider. Store an internal ID, issuer, subject, and creation timestamp; enforce uniqueness of `(issuer, subject)`. Do not create a login system.
- **Input context:** [`app/database.py`](../../../app/database.py) (`Base`, synchronous session); [`app/models/link.py`](../../../app/models/link.py) (typed `Mapped`/`mapped_column` style); [`app/models/__init__.py`](../../../app/models/__init__.py); [`migrations/env.py`](../../../migrations/env.py) (`target_metadata` imports); current revisions under [`migrations/versions/`](../../../migrations/versions/); [`tests/test_api.py`](../../../tests/test_api.py) (test style); [`requirements.txt`](../../../requirements.txt); [`alembic.ini`](../../../alembic.ini). Also inspect the approved identity-contract decision before coding.
- **Expected output:** Create `app/models/user.py`; update `app/models/__init__.py`; create one new Alembic revision under `migrations/versions/`; add `tests/test_user_model.py`.
- **External acceptance criteria:** On an isolated database, migration upgrade creates the user table and unique issuer/subject constraint; inserting two rows with the same pair is rejected; distinct pairs persist and can be queried; downgrade removes the new table cleanly. Alembic sees the model through the existing metadata import.
- **Dependencies:** Product/identity gates above must be resolved; existing shared `Base` and current Alembic head.
- **Change budget:** 130 changed lines maximum.

### TC-02 — Resolve requests to an authenticated user

- **Scope and purpose:** Integrate the approved verifier and expose a fail-closed FastAPI dependency that validates the incoming credential and resolves/upserts the corresponding local user. Invalid, missing, expired, wrong-issuer, or wrong-audience credentials must not become an authenticated principal.
- **Input context:** [`app/main.py`](../../../app/main.py) (current `Depends` usage); [`app/database.py`](../../../app/database.py) (`get_db`); [`app/models/user.py`](../../../app/models/user.py) and [`app/models/__init__.py`](../../../app/models/__init__.py) from `TC-01`; [`requirements.txt`](../../../requirements.txt); [`tests/test_api.py`](../../../tests/test_api.py); approved provider contract.
- **Expected output:** Create `app/auth.py`; create `tests/test_auth.py`; modify `requirements.txt` only if a reviewed provider integration requires an additional maintained verifier, with explicit approval.
- **External acceptance criteria:** A valid provider credential resolves the same local user for the same issuer/subject; invalid/missing/expired credentials receive HTTP 401; verifier/key/configuration failures fail closed and surface an explicit server error rather than authenticating; no route trusts caller-supplied user IDs or unverified headers. Unit tests may stub the verifier, but include a verification test using the provider's supported test keys/fixture if available.
- **Dependencies:** `TC-01`; approved provider/verifier and its deployment configuration contract. **Blocked until identity gate is resolved.**
- **Change budget:** 140 changed lines maximum. If provider wiring exceeds this, split provider verification from local-user resolution.

### TC-03 — Add the team entity

- **Scope and purpose:** Define a minimal team table with generated ID, bounded non-empty name, and creation timestamp. Do not add guessed project/link ownership fields.
- **Input context:** [`app/database.py`](../../../app/database.py); [`app/models/user.py`](../../../app/models/user.py) from `TC-01`; [`app/models/link.py`](../../../app/models/link.py); [`app/models/__init__.py`](../../../app/models/__init__.py); [`migrations/env.py`](../../../migrations/env.py); latest migration under [`migrations/versions/`](../../../migrations/versions/); [`tests/test_api.py`](../../../tests/test_api.py).
- **Expected output:** Create `app/models/team.py`; update `app/models/__init__.py`; add a new linear Alembic revision; create `tests/test_team_model.py`.
- **External acceptance criteria:** Migration creates the team table; valid team names persist; invalid/empty values are rejected at the agreed validation boundary; upgrade/downgrade pass on the isolated PostgreSQL test database.
- **Dependencies:** `TC-01`, `TC-02`, and product scope gate. Keep the migration on the current linear revision head.
- **Change budget:** 120 changed lines maximum.

### TC-04 — Persist team membership and roles

- **Scope and purpose:** Add a join model connecting users and teams, with unique `(team_id, user_id)`, a constrained role value (`owner`, `admin`, `member`), and creation time. Enforce at most one owner per team with a PostgreSQL constraint/index if compatible with the migration/test target; ensure creation logic maintains at least one owner.
- **Input context:** [`app/database.py`](../../../app/database.py); [`app/models/user.py`](../../../app/models/user.py); [`app/models/team.py`](../../../app/models/team.py); [`app/models/__init__.py`](../../../app/models/__init__.py); [`migrations/env.py`](../../../migrations/env.py); latest revision; [`tests/test_team_model.py`](../../../tests/test_team_model.py).
- **Expected output:** Create `app/models/team_membership.py`; update model exports; add a linear migration; create `tests/test_team_membership_model.py`.
- **External acceptance criteria:** Foreign keys reject nonexistent teams/users; duplicate membership is rejected; only supported roles persist; a team cannot acquire multiple owners; migration upgrade/downgrade pass on the isolated test database.
- **Dependencies:** `TC-03` and `TC-01`.
- **Change budget:** 140 changed lines maximum.

### TC-05 — Centralize team role authorization

- **Scope and purpose:** Implement reusable fail-closed policy/dependency helpers for membership lookup and role checks. Proposed minimum policy: all roles may read their team; only owner/admin may manage ordinary members and invitations; only owner may grant/revoke admin. Do not trust role/team IDs from request bodies without checking stored membership. Ownership transfer is out of the initial scope.
- **Input context:** `app/auth.py` and `tests/test_auth.py` from `TC-02`; [`app/database.py`](../../../app/database.py); `app/models/team.py`, `app/models/team_membership.py`; [`app/main.py`](../../../app/main.py) current dependency pattern.
- **Expected output:** Create `app/team_authorization.py`; create `tests/test_team_authorization.py`.
- **External acceptance criteria:** Tests prove each role's allowed/denied actions, cross-team IDs cannot grant access (HTTP 404 or 403 per documented policy), and missing membership is denied. No role is inferred from caller input.
- **Dependencies:** `TC-02`, `TC-03`, `TC-04`.
- **Change budget:** 120 changed lines maximum.

### TC-06 — Add append-only team activity records

- **Scope and purpose:** Add a minimal activity/audit entity with team, actor, event type, timestamp, and bounded structured metadata. Add no public mutation route for audit rows and exclude secrets/credentials from metadata.
- **Input context:** [`app/database.py`](../../../app/database.py); user/team/membership models from `TC-01`, `TC-03`, `TC-04`; [`app/models/__init__.py`](../../../app/models/__init__.py); [`migrations/env.py`](../../../migrations/env.py); latest Alembic revision; [`tests/test_api.py`](../../../tests/test_api.py).
- **Expected output:** Create `app/models/team_activity.py`; update model exports; add one linear Alembic revision; create `tests/test_team_activity_model.py`.
- **External acceptance criteria:** Activity rows reference an existing team and actor; event type and timestamp persist; no invitation token or authentication credential is stored; migration upgrade/downgrade pass on the isolated test database.
- **Dependencies:** `TC-04`, `TC-01`.
- **Change budget:** 140 changed lines maximum.

### TC-07 — Add authenticated team creation and retrieval

- **Scope and purpose:** Add team create, list-my-teams, and get-team endpoints. Team creation must atomically create the team, its owner membership, and a `team.created` activity entry. Listing and retrieval are scoped to the authenticated member.
- **Input context:** [`app/main.py`](../../../app/main.py) (direct `@app` route style and `Depends`); [`app/schemas.py`](../../../app/schemas.py); [`app/database.py`](../../../app/database.py); `app/auth.py`; team/membership/activity models; `app/team_authorization.py`; [`tests/test_api.py`](../../../tests/test_api.py).
- **Expected output:** Modify `app/main.py` and `app/schemas.py`; create `tests/test_teams_api.py`.
- **External acceptance criteria:** `POST /teams` returns 201 with team representation; authenticated creator is an owner; list returns only that user's teams; member can `GET /teams/{team_id}`; non-member cannot read it; rollback leaves no team, membership, or audit row if any part of creation fails.
- **Dependencies:** `TC-02` through `TC-06`.
- **Change budget:** 145 changed lines maximum; split read endpoints from create if necessary.

### TC-08 — Add member management endpoints

- **Scope and purpose:** Allow authorized owners/admins to list members and add/remove members or change roles. Enforce owner-only privileged role changes and prevent removal/demotion of the last owner.
- **Input context:** [`app/main.py`](../../../app/main.py); [`app/schemas.py`](../../../app/schemas.py); auth dependency; membership model; `app/team_authorization.py`; activity model; [`tests/test_api.py`](../../../tests/test_api.py).
- **Expected output:** Modify `app/main.py` and `app/schemas.py`; create `tests/test_team_members_api.py`.
- **External acceptance criteria:** Allowed changes return documented 2xx responses and persist membership; unauthorized roles receive 403; cross-team member IDs disclose no other team's data; duplicate add is handled predictably; last-owner removal/demotion is rejected; each successful mutation and no failed mutation is recorded as activity in the same transaction.
- **Dependencies:** `TC-04`, `TC-05`, `TC-06`.
- **Change budget:** 150 changed lines maximum; split role changes and member removal if necessary.

### TC-09 — Persist secure invitation state

- **Scope and purpose:** Add invitation persistence with team and creator references, unique token digest, bounded expiry, creation time, optional revoked/accepted timestamps and accepting user. Do not persist the raw token. Model pending/revoked/accepted/expired state consistently and prevent multiple terminal transitions.
- **Input context:** [`app/database.py`](../../../app/database.py); `app/models/user.py`, `app/models/team.py`, `app/models/team_membership.py`, `app/models/team_activity.py`; exports; [`migrations/env.py`](../../../migrations/env.py); latest revision; [`requirements.txt`](../../../requirements.txt) (use standard `secrets`/`hashlib` unless approved security review requires otherwise).
- **Expected output:** Create `app/models/team_invitation.py`; update model exports; add one linear Alembic revision; create `tests/test_team_invitation_model.py`.
- **External acceptance criteria:** Unique digest constraint works; expired/revoked/accepted state is distinguishable; only digest is stored; foreign keys and migration upgrade/downgrade pass on isolated PostgreSQL.
- **Dependencies:** `TC-06`, `TC-04`, `TC-01`; invitation-delivery decision above.
- **Change budget:** 145 changed lines maximum.

### TC-10 — Issue and revoke invitations

- **Scope and purpose:** Add owner/admin-protected invitation issuance and revocation. Generate a high-entropy bearer token, store only its digest, enforce a maximum expiry, return the raw token only in the issuance response, and never log/audit it.
- **Input context:** [`app/main.py`](../../../app/main.py); [`app/schemas.py`](../../../app/schemas.py); auth and team authorization dependencies; invitation/activity models; [`app/database.py`](../../../app/database.py); [`tests/test_team_members_api.py`](../../../tests/test_team_members_api.py).
- **Expected output:** Modify `app/main.py` and `app/schemas.py`; create `tests/test_team_invitations_api.py`.
- **External acceptance criteria:** Authorized issuance returns the raw token once and stores only a digest; member/non-member issuance is denied; requested expiry outside policy is rejected; revocation succeeds only for the inviter-authorized team and pending invitation; revoked token cannot be accepted; successful issue/revoke emits activity in the same transaction; except for the one-time issuance response, persisted records and logs contain no raw token.
- **Dependencies:** `TC-05`, `TC-06`, `TC-09`; identity and delivery gates.
- **Change budget:** 150 changed lines maximum; split revocation from issuance if necessary.

### TC-11 — Redeem an invitation exactly once

- **Scope and purpose:** Add an authenticated invitation-redemption endpoint. Hash the presented bearer token, atomically transition only a pending, unexpired, unrevoked invitation, create the member membership, and write the audit event in one transaction. Reject replay and concurrent duplicate redemption.
- **Input context:** [`app/main.py`](../../../app/main.py); [`app/schemas.py`](../../../app/schemas.py); `app/auth.py`; `app/database.py`; user, membership, invitation, and activity models; `app/team_authorization.py`; [`tests/test_team_invitations_api.py`](../../../tests/test_team_invitations_api.py).
- **Expected output:** Modify `app/main.py` and `app/schemas.py`; add redemption cases to `tests/test_team_invitations_api.py`.
- **External acceptance criteria:** First valid authenticated redemption creates exactly one membership and marks the invitation accepted; unknown, expired, revoked, previously accepted, and concurrently replayed tokens create no additional membership and return documented errors; failures roll back state and audit changes; logs contain no token.
- **Dependencies:** `TC-02`, `TC-04`, `TC-05`, `TC-06`, `TC-09`, `TC-10`.
- **Change budget:** 150 changed lines maximum; split concurrency handling into a separate task if needed.

### TC-12 — Expose a member-scoped activity feed

- **Scope and purpose:** Add a read-only, paginated team activity endpoint. Only current team members can read it; return safe metadata and stable chronological ordering/cursor semantics.
- **Input context:** [`app/main.py`](../../../app/main.py); [`app/schemas.py`](../../../app/schemas.py); auth/authorization helpers; activity model; [`app/database.py`](../../../app/database.py); [`tests/test_teams_api.py`](../../../tests/test_teams_api.py).
- **Expected output:** Modify `app/main.py` and `app/schemas.py`; create `tests/test_team_activity_api.py`.
- **External acceptance criteria:** Members see only their team's events in deterministic order with bounded pagination; non-members are denied; response omits internal secrets and raw invitation tokens; no write operation to the activity feed is exposed.
- **Dependencies:** `TC-05`, `TC-06`, `TC-07`.
- **Change budget:** 130 changed lines maximum.

## 4. Full copy-paste-ready prompts for the first three tasks

### Prompt for TC-01 — Persist verified external user identities

```text
Implement only task TC-01 from progress/ai-augmented-engineering/module-02/task-tree.md: persist verified external user identities.

Context files to inspect before editing:
- app/database.py: shared SQLAlchemy Base and synchronous database setup
- app/models/link.py: existing typed Mapped/mapped_column model style
- app/models/__init__.py: model exports
- migrations/env.py: model imports and Base.metadata wiring
- every current file under migrations/versions/: find the actual latest revision and preserve one linear chain
- tests/test_api.py: existing pytest/FastAPI test conventions and database coupling
- requirements.txt and alembic.ini: existing dependencies and migration configuration
- the approved identity-contract decision produced by the product/security prerequisite gate

Verified constraints:
- There is no existing User model or authentication system.
- The current application is a FastAPI URL shortener, not a project-management application.
- Do not read .env or credential files, print connection strings, or run migrations against an unknown database.
- Existing models inherit from app.database.Base and are exported from app.models.

Deliverables, and no others:
1. Create app/models/user.py with a minimal User table containing an internal integer primary key, trusted identity issuer, stable trusted identity subject, and UTC creation time. Add a database uniqueness constraint for (issuer, subject).
2. Export User from app/models/__init__.py and ensure migrations/env.py imports it through the existing model import path so Alembic metadata contains the table.
3. Add exactly one Alembic revision in migrations/versions/ with correct revision/down_revision based on the actual current head. Implement upgrade and downgrade.
4. Add tests/test_user_model.py using only an explicitly isolated disposable test database.

Conventions and limits:
- Follow the existing SQLAlchemy typed Mapped/mapped_column style and migration formatting.
- Do not add an ORM relationship unless it is required by observed implementation needs.
- Do not add email, password, login, token, or provider-specific columns unless the approved identity contract requires them; explain and stop for review if so.
- User records may only be created from a principal whose issuer and subject have already been verified by the approved identity integration. Never accept a caller-supplied user ID as identity.
- Do not add dependencies or edit application routes.
- Maximum total diff: 130 changed lines across all files. If the task exceeds this budget, stop and propose a smaller split before making more changes.

Acceptance criteria:
- On the isolated PostgreSQL test database, the migration upgrade creates the table and unique issuer/subject constraint; downgrade removes it.
- A test proves a valid identity pair can be stored and queried and a duplicate pair is rejected; distinct issuer/subject pairs are permitted.
- Alembic metadata includes User after normal migrations/env.py imports.
- Focused tests pass without reading .env, modifying existing demo records, or relying on production data.

If the identity-contract decision is missing or unresolved, do not guess: make no changes and report the exact provider/identity decisions needed. After implementation, report files changed, migration revision, test command/results, and changed-line count.
```

### Prompt for TC-02 — Resolve requests to an authenticated user

```text
Implement only task TC-02 from progress/ai-augmented-engineering/module-02/task-tree.md: resolve requests to an authenticated user.

Context files to inspect before editing:
- app/main.py: current FastAPI app and Depends usage
- app/database.py: get_db session dependency
- app/auth.py if it exists from an earlier partial implementation; otherwise confirm it does not exist
- app/models/user.py and app/models/__init__.py from TC-01
- requirements.txt: installed packages; do not assume JWT/auth libraries are present
- tests/test_api.py and tests/test_user_model.py: test client and isolated database conventions
- the approved identity-provider contract, verifier documentation, deployment configuration contract, and TC-01 implementation results

Verified constraints:
- No authentication/authorization system or User model existed in the original codebase.
- Do not read .env or credential files, expose key material, or trust client-supplied identity headers/user IDs.
- Existing route functions use synchronous def handlers and FastAPI Depends(get_db).

Deliverables, and no others:
1. Create app/auth.py with a typed authenticated-principal dependency that uses the approved provider's maintained verifier, validates issuer/audience/signature/expiry per the approved contract, and resolves the local User by verified issuer/subject.
2. Create tests/test_auth.py covering valid and invalid credentials using isolated test fixtures and provider-supported test keys or a test verifier seam.
3. Modify requirements.txt only if the approved provider integration truly requires a new maintained verifier package and that dependency has been explicitly approved. Do not add a new framework.

Conventions and limits:
- Missing, malformed, expired, wrong-issuer, or wrong-audience credentials must fail closed with HTTP 401.
- Verifier/configuration failures must not silently authenticate or return a success-shaped fallback; surface a clear server error.
- Never decode a JWT and treat its claims as trusted without cryptographic and claim validation. Never trust arbitrary forwarded headers unless the deployment contract proves a trusted proxy strips/replaces them and that contract is tested.
- Do not add login/signup endpoints, protect unrelated existing routes, or change Link behavior in this task.
- Do not log bearer tokens or claims beyond safe identifiers.
- Maximum total diff: 140 changed lines. If provider integration cannot fit, split verifier construction from local-user resolution.

Acceptance criteria:
- A valid test credential resolves the expected persisted User for its verified issuer/subject.
- Missing/invalid/expired/wrong-issuer/wrong-audience credentials return 401 and never resolve a User.
- Tests use a disposable database and never depend on demo data.
- No new dependency is added without explicit approval.

If no approved provider/verifier or trustworthy runtime contract exists, do not build a placeholder, mock-only production path, custom cryptography, or static identity. Make no changes; report the missing prerequisite and stop. After implementation, report deliverables, verifier choice, test command/results, and changed-line count.
```

### Prompt for TC-03 — Add the team entity

```text
Implement only task TC-03 from progress/ai-augmented-engineering/module-02/task-tree.md: add the team entity.

Context files to inspect before editing:
- app/database.py: shared Base and session style
- app/models/link.py: existing SQLAlchemy model conventions
- app/models/user.py and app/models/__init__.py from TC-01
- app/models/__init__.py: current exports after TC-01/TC-02
- migrations/env.py and every file in migrations/versions/: metadata wiring and actual Alembic head
- tests/test_api.py and tests/test_user_model.py: existing test/database conventions
- product decision resolving whether this repository and a generic team foundation are in scope
- TC-01 and TC-02 implementation results; verify actual file contents rather than assuming this plan was followed exactly

Verified constraints:
- The repository is a URL shortener; no Project or Task model exists.
- Custom routes currently live in app/main.py, while this task adds no routes.
- Do not read .env or credentials or run schema changes on an unknown database.

Deliverables, and no others:
1. Create app/models/team.py with a minimal Team table: integer primary key, non-empty bounded name, and UTC creation timestamp. Do not invent project/link ownership fields.
2. Export Team from app/models/__init__.py so migrations/env.py's existing model import makes it visible to Base.metadata.
3. Add one new Alembic revision under migrations/versions/ chained to the actual latest revision, with upgrade and downgrade.
4. Add tests/test_team_model.py using the isolated disposable PostgreSQL test database.

Conventions and limits:
- Follow app/models/link.py's typed Mapped/mapped_column style and the existing migration format.
- Do not introduce SQLAlchemy async APIs, a new router framework, unrelated models, or dependencies.
- Avoid ORM relationship() properties unless they are demonstrably needed by the inspected consumers.
- Maximum total diff: 120 changed lines. If schema and tests exceed this limit, stop and split the task.

Acceptance criteria:
- Isolated-database migration upgrade creates the team table and downgrade removes it.
- Tests verify valid team persistence, name validation at the agreed boundary, and safe rollback.
- The new model is present in Alembic target metadata through existing imports.
- Existing Link and ClickEvent definitions and behavior are unchanged.

If product scope is unresolved or the current Alembic head differs from the plan, stop and report the discrepancy rather than guessing. After implementation, report files changed, actual parent/new revision IDs, focused test command/results, and changed-line count.
```

## 5. Dependency order, path length, risks, and cross-cutting checks

### Valid topological implementation order

One valid ordering that respects the dependencies declared for all 12 tasks is:

`TC-01` → `TC-02` → `TC-03` → `TC-04` → `TC-05` → `TC-06` → `TC-07` → `TC-08` → `TC-09` → `TC-10` → `TC-11` → `TC-12`.

This is a valid serial implementation order, not a requirement to execute independent tasks serially. In particular, `TC-07` and `TC-08` may be scheduled in parallel once their own declared dependencies are complete. `TC-12` depends on `TC-05`, `TC-06`, and `TC-07`; it does not depend on invitation tasks `TC-09` through `TC-11`.

Alembic revision tasks must remain serialized in this order: `TC-01` → `TC-03` → `TC-04` → `TC-06` → `TC-09`. This migration-only ordering is subject to the full task dependencies (for example, `TC-03` also requires `TC-02`). Other code/test work may be parallelized only after its declared dependencies and file ownership are clear.

### Longest dependency chain by task count

The longest chain in the documented dependency graph contains **8 tasks**:

`TC-01` → `TC-02` → `TC-03` → `TC-04` → `TC-06` → `TC-09` → `TC-10` → `TC-11`.

This count measures dependency steps by number of tasks, not elapsed time. `TC-12` is not part of this chain; it can complete after `TC-07` and does not wait on invitations.

### Time-based critical path status

A rigorously calculated, time-based critical path **has not been established**. Task durations and resource constraints have not been estimated, so the longest chain by task count must not be interpreted as the critical path by elapsed time.

### Riskiest task

**`TC-02` is the highest-risk task.** The current repository has no identity verifier, provider configuration, key-rotation process, or user principal. A plausible but unverified token/header implementation could let an attacker impersonate users, undermining every team authorization decision. It is intentionally blocked on an explicit provider/runtime contract and must fail closed. Invitation redemption (`TC-11`) is the next highest risk because concurrency, expiry, revocation, and replay must be enforced atomically.

### Cross-cutting concerns and release checks

- **Authorization / IDOR:** Derive actor identity only from the verified auth dependency. Check membership and role for every team-scoped read and mutation; never authorize from a supplied `user_id`, team role, or guessed resource identifier. Use one documented 403/404 policy consistently.
- **Invitation replay and secrecy:** Generate a high-entropy token; store only a digest; set a maximum lifetime; make revocation and acceptance terminal; use a conditional DB state transition so concurrent redeemers cannot both succeed. Return the raw token only once, never include it in activity metadata/logging, and acknowledge bearer forwarding risk while no email/recipient identity binding exists.
- **Transaction consistency:** Team plus initial owner plus activity record; membership mutation plus activity; invitation issuance/revocation/redemption plus activity must each commit or roll back atomically. Use database uniqueness/constraints to backstop application checks.
- **Auditability:** Activity is append-only from the API perspective. Record actor, team, event, timestamp, and safe target metadata. Do not store credentials, raw invitation tokens, or unnecessary personal data.
- **Ownership invariants:** A team must never be left without an owner; restrict owner removal/demotion. Ownership transfer is excluded from this initial plan and requires its own explicit atomic task if requested. Enforce uniqueness in the database where supported, not only in request validation.
- **Migrations and tests:** Keep one Alembic head, inspect `down_revision` before each new migration, verify upgrade/downgrade on disposable PostgreSQL, and keep tests isolated from existing demo rows. Never read or edit `.env` to make tests pass.
- **Scope creep:** Do not attach teams to links, invent project/task models, add email, job queues, or a new web framework unless the product owner explicitly expands scope and the corresponding infrastructure is designed.
- **Line budgets:** Recount changed lines for every task before handoff; split immediately when a task exceeds 150 lines.

## Module 02 BREAK — Conflicting Assumption Investigation

The supplied mismatch—Task 1 creating a teams table with `owner_id` while Task 2 assumes an existing `team_members` join table with a role field—does **not** directly apply to documented `TC-01` and `TC-02`.

- `TC-01` creates the `User` identity model with an internal ID, issuer, subject, and creation timestamp, including uniqueness of `(issuer, subject)`.
- `TC-02` consumes the authenticated identity and resolves/upserts the corresponding local user. It does not assume or introduce a teams table, `team_members` table, or team role field.
- Team membership and roles are introduced later in `TC-04`, which defines the membership model and its `owner`, `admin`, and `member` roles.

The closest real ambiguity is the handoff between `TC-01` creating and migrating the user model and `TC-02` resolving/upserting that model during authentication. To avoid drift, the `TC-02` prompt should explicitly require consuming the exact fields and `(issuer, subject)` uniqueness constraint produced by `TC-01`, and prohibit adding team or membership schema. The approved identity-provider verification contract—including how issuer and subject are trusted—must be resolved before implementation; neither task should invent an identity source or verifier.

This was an investigation only. No implementation prompt was executed, and no application code, migrations, tests, database records, or configuration were changed.
