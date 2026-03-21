# Development Workflow

When implementing changes to the application, follow this checklist in order:

1. **Requirements** — Update `requirements.md` if the change affects functional, non-functional, or technical requirements.
2. **Solution Design** — Update `solution_design.md` to reflect any architectural or API changes.
3. **Implementation** — Make the code changes in `lambda/` and/or `frontend/`.
4. **Unit Tests** — Update or add tests in `lambda/test_handler.py`. Run with `python -m pytest lambda/test_handler.py -v`.
5. **Deploy** — Run `./deploy.sh lambda`, `./deploy.sh frontend`, or `./deploy.sh all`.
6. **Integration Test** — Verify the live endpoint at `https://jobbet.mulmo.name/api/routes` returns expected data, and check the frontend at `https://jobbet.mulmo.name`.

Do not skip steps. Every change should flow through the full cycle.
