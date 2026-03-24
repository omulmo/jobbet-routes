#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/cdk"

echo "→ Bootstrapping CDK..."
CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_ACCOUNT

HOSTNAME="${1:-trips.mulmo.name}"
CDK_CONTEXT="-c hostname=$HOSTNAME"

./node_modules/.bin/cdk bootstrap "aws://$CDK_DEFAULT_ACCOUNT/us-east-1" "aws://$CDK_DEFAULT_ACCOUNT/eu-north-1"

echo "→ Deploying infrastructure..."
./node_modules/.bin/cdk deploy --all --require-approval never $CDK_CONTEXT

echo "→ Saving resource names..."
STACK="TripsAppStack"
REGION="eu-north-1"

cat > ../deploy.env <<EOF
REGION=$REGION
LAMBDA_NAME=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id Handler886CB40B --region $REGION --query StackResourceDetail.PhysicalResourceId --output text)
S3_BUCKET=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id Frontend23D93C55 --region $REGION --query StackResourceDetail.PhysicalResourceId --output text)
CF_DIST=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id CDN2330F4C0 --region $REGION --query StackResourceDetail.PhysicalResourceId --output text)
EOF

echo "✅ Infrastructure deployed. Resource names saved to deploy.env"
cat ../deploy.env
