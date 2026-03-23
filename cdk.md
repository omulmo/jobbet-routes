# Jobbet CDK Deployment — Teardown Reference

The Jobbet app (`jobbet.mulmo.name`) is a separate deployment that predates the Trips app. These identifiers are recorded here so the Jobbet stacks can be torn down later.

## Stacks

| Stack | Region |
|-------|--------|
| `JobbetCertificateStack` | us-east-1 |
| `JobbetAppStack` | eu-north-1 |

## Physical Resources (from deploy.env)

```
LAMBDA_NAME=JobbetAppStack-Handler886CB40B-1vVCXfGXx59D
S3_BUCKET=jobbetappstack-frontend23d93c55-kye3beahbdq3
CF_DIST=E3397XDD1P8ZZH
```

## Other

| Item | Value |
|------|-------|
| AWS Account | `362136510829` |
| Hosted Zone | `Z25WPVEDBA545` (`mulmo.name`) |
| Tag | `Project: JobbetApp` |

## Teardown

```bash
cd cdk
CDK_DEFAULT_ACCOUNT=362136510829 ./node_modules/.bin/cdk destroy --all
```
