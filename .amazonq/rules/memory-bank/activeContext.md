# Active Context

## Current Focus
- Application is deployed and live at https://jobbet.mulmo.name
- Iterating on Lambda handler and frontend

## Recent Changes
- Deployed full infrastructure via CDK (two stacks across us-east-1 and eu-north-1)
- Fixed CloudFront → Lambda 403 by adding OAC (`FunctionUrlOrigin.withOriginAccessControl`)
- Added `lambda:InvokeFunction` permission (required since Oct 2025, in addition to `lambda:InvokeFunctionUrl`)
- Made hostname configurable via CDK context (defaults to `jobbet.mulmo.name`)
- Created fast deploy script (`deploy.sh`) and infrastructure setup script (`setup-infrastructure.sh`)
- Removed nested `.git` in `cdk/`, initialized repo, pushed to github.com/omulmo/jobbet-routes.git

## Next Steps
- Iterate on Lambda handler logic and frontend UI
- Test real-time route data from SL Journey Planner v2 API

## Active Decisions
- Using `deploy.sh` for fast code iteration (bypasses CloudFormation)
- Using `setup-infrastructure.sh` for full CDK deploys
- Resource names stored in `deploy.env` (gitignored)
