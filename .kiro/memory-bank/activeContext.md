# Active Context

## Current Focus
- Application is deployed and live at https://jobbet.mulmo.name
- Iterating on Lambda handler and frontend

## Recent Changes
- Added structured logging to Lambda handler (route skips, API failures, zero-routes warning, route count)
- Added commit workflow to development-workflow.md: reflect → update memory bank → commit
- Updated dev_server.py mock with real SL API data and fixed emoji encoding (ZWJ characters)
- Added `kiro.sh` launcher and `.kiro/agents/jobbet.json` agent config with whitelisted tools and shell commands
- Added `Project: JobbetApp` tag to all AWS resources (NFR-6) via `cdk.Tags.of(app).add()` in `cdk/bin/app.ts`
- Deployed full infrastructure via CDK (two stacks across us-east-1 and eu-north-1)
- Fixed CloudFront → Lambda 403 by adding OAC (`FunctionUrlOrigin.withOriginAccessControl`)
- Added `lambda:InvokeFunction` permission (required since Oct 2025, in addition to `lambda:InvokeFunctionUrl`)
- Made hostname configurable via CDK context (defaults to `jobbet.mulmo.name`)
- Created fast deploy script (`deploy.sh`) and infrastructure setup script (`setup-infrastructure.sh`)
- Removed nested `.git` in `cdk/`, initialized repo, pushed to github.com/omulmo/jobbet-routes.git

## Next Steps
- Iterate on Lambda handler logic and frontend UI
- Test real-time route data from SL Journey Planner v2 API

## Workflow Reminders
- On commit: ALWAYS read `.kiro/agents/development-workflow.md` first and follow all steps (reflect → update memory bank → commit)

## Active Decisions
- Using `deploy.sh` for fast code iteration (bypasses CloudFormation)
- Using `setup-infrastructure.sh` for full CDK deploys
- Resource names stored in `deploy.env` (gitignored)
