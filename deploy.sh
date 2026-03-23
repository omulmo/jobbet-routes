#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE="deploy.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found. Run ./setup-infrastructure.sh first." >&2
  exit 1
fi
source "$ENV_FILE"

deploy_lambda() {
  echo "→ Deploying Lambda..."
  rm -rf /tmp/lambda-pkg /tmp/lambda.zip
  mkdir /tmp/lambda-pkg
  pip install -q -r lambda/requirements.txt -t /tmp/lambda-pkg
  cp lambda/*.py /tmp/lambda-pkg/
  (cd /tmp/lambda-pkg && zip -qr /tmp/lambda.zip .)
  aws lambda update-function-code \
    --function-name "$LAMBDA_NAME" \
    --zip-file fileb:///tmp/lambda.zip \
    --region "$REGION" \
    --no-cli-pager
  echo "✅ Lambda updated"
}

deploy_frontend() {
  echo "→ Deploying frontend..."
  aws s3 sync frontend/ "s3://$S3_BUCKET/" --region "$REGION" --delete
  aws cloudfront create-invalidation \
    --distribution-id "$CF_DIST" \
    --paths "/*" \
    --region "$REGION" \
    --no-cli-pager
  echo "✅ Frontend deployed"
}

case "${1:-}" in
  lambda)   deploy_lambda ;;
  frontend) deploy_frontend ;;
  all)
    deploy_lambda &
    deploy_frontend &
    wait
    echo "✅ All deployed"
    ;;
  *)
    echo "Usage: ./deploy.sh {lambda|frontend|all}"
    exit 1
    ;;
esac
