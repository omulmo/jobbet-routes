# Tech Context

## Technologies
- Frontend: HTML + CSS + vanilla JS (no framework, no build step)
- Backend: Python 3.12 Lambda function (uses `zoneinfo.ZoneInfo("Europe/Stockholm")` for timezone)
- Infrastructure: AWS CDK (TypeScript) with aws-cdk-lib 2.244.0
- External API: SL Journey Planner v2 (no API key required)

## AWS Architecture
- **JobbetCertificateStack** (us-east-1): ACM certificate for custom domain, DNS-validated via Route 53
- **JobbetAppStack** (eu-north-1): S3 bucket, Lambda + function URL (IAM auth), CloudFront distribution, Route 53 alias
- CloudFront OAC for both S3 and Lambda origins
- Hostname configurable via CDK context (`-c hostname=...`), defaults to `jobbet.mulmo.name`
- Hosted zone (`mulmo.name`) derived by stripping first subdomain label from hostname
- Note: domain will change to `trips.mulmo.name` — CDK/infra updates pending solution design

## Key Learnings
- `FunctionUrlOrigin.withOriginAccessControl(fnUrl)` is required for CloudFront → Lambda function URL with IAM auth (plain `new FunctionUrlOrigin()` causes 403)
- Since October 2025, Lambda function URLs need both `lambda:InvokeFunctionUrl` AND `lambda:InvokeFunction` permissions — CDK's OAC only adds the former, so `lambda:InvokeFunction` must be added manually via `fn.addPermission()`
- `npx cdk` in this project swallows stdout; use `./node_modules/.bin/cdk` directly
- CDK requires `CDK_DEFAULT_ACCOUNT` env var since stacks use explicit account/region
- CloudFront `/api/*` behavior already forwards query strings to Lambda via `ALL_VIEWER_EXCEPT_HOST_HEADER` origin request policy — no CDK changes needed for query param support

## Deployment
- `./setup-infrastructure.sh [hostname]` — CDK bootstrap + deploy, saves resource names to `deploy.env`
- `./deploy.sh lambda|frontend|all` — fast deploys bypassing CloudFormation (~5-10s)
- `deploy.env` contains REGION, LAMBDA_NAME, S3_BUCKET, CF_DIST (gitignored)

## Repository
- Git repo: git@github.com:omulmo/jobbet-routes.git
- Branch: main
