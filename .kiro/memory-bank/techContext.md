# Tech Context

## Technologies
- Frontend: HTML + CSS + vanilla JS (no framework, no build step)
- Backend: Python 3.12 Lambda function (uses `zoneinfo.ZoneInfo("Europe/Stockholm")` for timezone)
- Infrastructure: AWS CDK (TypeScript) with aws-cdk-lib
- External API: SL Journey Planner v2 (no API key required)
- Persistence: S3 single JSON document (`state.json` in private bucket)
- Validation: jsonschema (single source of truth for input validation)

## AWS Architecture
- **CertificateStack** (us-east-1): ACM certificate (currently `jobbet.mulmo.name`, will become `trips.mulmo.name`)
- **AppStack** (eu-north-1): S3 frontend bucket, S3 state bucket, Lambda + function URL, CloudFront, Route 53, Secrets Manager
- CloudFront OAC for both S3 and Lambda origins
- All resources tagged `Project: TripsApp`
- CDK stack names still `JobbetCertificateStack`/`JobbetAppStack` (rename is increment 7)

## Key Learnings
- `FunctionUrlOrigin.withOriginAccessControl(fnUrl)` required for CloudFront → Lambda function URL with IAM auth
- Lambda function URLs need both `lambda:InvokeFunctionUrl` AND `lambda:InvokeFunction` permissions since Oct 2025
- `npx cdk` swallows stdout; use `./node_modules/.bin/cdk` directly
- CDK requires `CDK_DEFAULT_ACCOUNT` env var since stacks use explicit account/region
- CloudFront `/api/*` behavior forwards query strings via `ALL_VIEWER_EXCEPT_HOST_HEADER` origin request policy
- SL stop-finder supports coordinate lookup: `name_sf=lon:lat:WGS84[dd.ddddd]&type_sf=coord` (longitude first)
- ZWJ right-facing emoji trick (`\u200D\u27A1\uFE0F`) only works on person emojis, not vehicles
- `deploy.sh` must use `pip3` (not `pip`) and include `*.json` files in Lambda package
- Kiro CLI bash tool cannot run long-lived background processes — test APIs by calling handler directly in Python
- S3 state with `default_state.json` fallback eliminates need for a seeding step

## Deployment
- `./setup-infrastructure.sh [hostname]` — CDK bootstrap + deploy, saves resource names to `deploy.env`
- `./deploy.sh lambda|frontend|all` — fast deploys bypassing CloudFormation (~5-10s)
- `deploy.env` contains REGION, LAMBDA_NAME, S3_BUCKET, CF_DIST
- Lambda bundling: CDK Docker bundling runs `pip install -r requirements.txt`
