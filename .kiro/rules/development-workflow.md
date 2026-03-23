# Development Workflow

Work is done in small, independently deployable increments. Each increment is a vertical slice through the stack. Follow this checklist in order:

1. **Requirements** — Update `requirements.md` if the change affects functional, non-functional, or technical requirements.
2. **Solution Design** — Update `solution_design.md` to reflect any architectural or API changes. This includes defining or extending domain primitives (entities, their attributes, relationships, and invariants) in the solution design document. The source code (`lambda/models.py`) implements these definitions but is not the source of truth.
3. **API-First Design** — Specify new or changed endpoints in `openapi.yaml` (request/response schemas, error codes) before writing any implementation.
4. **Implementation** — Build the backend endpoint, wire it in `handler.py`, and implement any supporting modules in `lambda/`.
5. **Unit Tests** — Add or update tests. Run with `cd lambda && python3 -m pytest -v`.
6. **Frontend** — Build the UI that consumes the new endpoint in `frontend/`.
7. **Local Verification** — Start `cd lambda && python3 dev_server.py` and verify in browser at `http://localhost:8000`.
8. **Deploy** — Run `./deploy.sh lambda`, `./deploy.sh frontend`, or `./deploy.sh all`.
9. **Integration Test** — Verify the live endpoint and frontend.

No stub endpoints. Features don't exist in the router until their increment builds them. Do not skip steps. Every change should flow through the full cycle.

## Coding Conventions

- **Emoji in Python**: Never use inline emoji literals. Define named unicode escape constants (e.g. `ICON_METRO = "\U0001f687"`) and reference those.

## Commit Workflow

When asked to commit, always do the following before running `git commit`:

1. **Reflect** — Review what was learned or changed during this work session.
2. **Update Memory Bank** — Update relevant `.kiro/memory-bank/` files (activeContext.md, systemPatterns.md, techContext.md, progress.md) with any new knowledge, decisions, patterns, or gotchas discovered.
3. **Stage & Commit** — Stage all changes (including memory bank updates) and commit with a descriptive message.
4. **Push** — Always `git push` immediately after committing.
