## Metis workflow

This project uses Metis — a lightweight toolset for keeping a project's intent, status, and history legible across agent sessions.

**State on disk** lives in `.metis/`:
- `BUILD.md` — what we're building (forward-looking architecture brief).
- `CURRENT.md` — session handoff. Read first on any new session.
- `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, `QUESTIONS.md`, `RESOLVED.md` — reconciliation artifacts for the project's `docs/` corpus (created when one exists).
- `config.yaml` — project name and Metis version pin.

**Workflow primitives** (type `/metis-` for the full list):
- `/metis-session-start` — load `.metis/CURRENT.md` and orient.
- `/metis-reconcile` — read `docs/`, surface contradictions and open questions.
- `/metis-build-spec` — produce `.metis/BUILD.md`.
- `/metis-plan-task`, `/metis-implement-task`, `/metis-review-task` — the per-task loop.
- `/metis-session-end` — update `.metis/CURRENT.md` for next session.

Plans live in chat by default; only `CURRENT.md` persists session-to-session continuity.
