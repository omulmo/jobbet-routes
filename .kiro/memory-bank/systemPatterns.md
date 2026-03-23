# System Patterns

## Architecture
- Two CDK stacks: CertificateStack (us-east-1) for ACM cert, AppStack (eu-north-1) for everything else
- Cross-stack reference: certificate ARN exported from CertificateStack, imported by AppStack
- CloudFront single distribution serves both S3 (static) and Lambda (API) via path-based routing
- S3 state bucket (private, BLOCK_ALL, RETAIN) for single JSON document persistence
- S3 frontend bucket (public via CloudFront, DESTROY) for static assets
- Layered Lambda: handler.py → routes.py → state.py → models.py

## Project Structure
```
kiro-dev-workshop/
├── cdk/                    # CDK infrastructure (TypeScript)
│   ├── bin/app.ts
│   ├── lib/certificate-stack.ts
│   └── lib/app-stack.ts
├── lambda/                 # Python Lambda
│   ├── handler.py          # HTTP routing (only wired endpoints)
│   ├── routes.py           # Route comparison logic
│   ├── state.py            # S3 state persistence (load/save)
│   ├── models.py           # Domain entities, schemas, validation, helpers
│   ├── default_state.json  # Initial state (Hemma/Jobbet)
│   └── dev_server.py       # Local dev server with in-memory state
├── frontend/               # Static HTML + CSS + JS
├── deploy.sh               # Fast code deploys
├── setup-infrastructure.sh # CDK bootstrap + deploy
├── deploy.env              # Resource names (generated)
├── requirements.md
├── solution_design.md
└── sl-api.md
```

## Development Workflow
Vertical slices: requirements → solution design (domain primitives) → API-first (OpenAPI) → implement → test → frontend → deploy. No stub endpoints.

## API Design (current)
- `GET /api/routes?trip=<id>&reverse=true` — route comparison

Additional endpoints built incrementally as vertical slices when needed.

## Conventions
- **Always use `python3`** (never `python`)
- **Always use a virtual environment (`venv`)** for Python work
- **Always use project scripts for deployments** — `./setup-infrastructure.sh` and `./deploy.sh`
- Use `./node_modules/.bin/cdk` instead of `npx cdk`
- `CDK_DEFAULT_ACCOUNT` derived from `aws sts get-caller-identity`, never hardcoded
- Emoji in Python code: use named `\uXXXX` constants — never inline emoji literals
- SL API station names: use `leg.origin.parent.disassembledName` for human-readable names
- Domain primitives defined in `solution_design.md`, implemented in `models.py`

## Testing Strategy
- Unit tests: pytest, mocked external deps, time-fixed tests
- Integration tests: local dev server on localhost:8000
- Smoke tests: curl against live deployment after deploy
