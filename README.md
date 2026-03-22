# Jobbet — jobbet.mulmo.name

A personal commuter app for Stockholm. Compares real-time public transit routes between home (Skarpnäck) and work (Solna station) in both directions, and recommends the fastest option.

## Architecture

```
Browser → jobbet.mulmo.name (Route 53)
       → CloudFront
           ├── /*      → S3 (static HTML + CSS + JS)
           └── /api/*  → Lambda Function URL (Python)
                            → SL Journey Planner v2 API
```

## Project Structure

```
├── frontend/           # Static site (index.html, style.css)
├── lambda/             # Python Lambda handler
├── cdk/                # AWS CDK infrastructure (TypeScript)
├── deploy.sh           # Fast deploy for code changes
├── setup-infrastructure.sh  # CDK bootstrap + deploy
├── requirements.md     # Functional & technical requirements
└── solution_design.md  # Detailed architecture & API docs
```

## Prerequisites

- AWS CLI configured with credentials
- Node.js (for CDK)
- Python 3.12+ (for Lambda development/testing)

## Development Conventions

- Always use `python3` (never `python`) when executing Python commands
- Always use a virtual environment (`venv`) for Python work

## Initial Setup

```bash
cd cdk && npm install && cd ..
./setup-infrastructure.sh                    # defaults to jobbet.mulmo.name
./setup-infrastructure.sh other.mulmo.name   # custom hostname
```

This bootstraps CDK in `us-east-1` and `eu-north-1`, deploys all infrastructure, and saves resource names to `deploy.env`.

## Deploying Code Changes

```bash
./deploy.sh lambda      # Update Lambda function (~5s)
./deploy.sh frontend    # Sync frontend to S3 + CloudFront invalidation (~10s)
./deploy.sh all         # Both in parallel
```

## Deploying Infrastructure Changes

When you modify CDK stacks (new resources, permissions, etc.):

```bash
cd cdk
CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text) ./node_modules/.bin/cdk deploy --all --require-approval never
```

## AWS Resources

Two CloudFormation stacks:

- **JobbetCertificateStack** (us-east-1) — ACM certificate for `jobbet.mulmo.name`
- **JobbetAppStack** (eu-north-1) — S3 bucket, Lambda, CloudFront, Route 53 alias
