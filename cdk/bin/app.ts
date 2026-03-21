import * as cdk from 'aws-cdk-lib';
import { CertificateStack } from '../lib/certificate-stack';
import { AppStack } from '../lib/app-stack';

const app = new cdk.App();
const hostname = app.node.tryGetContext('hostname') || 'jobbet.mulmo.name';
const hostedZoneDomain = hostname.split('.').slice(1).join('.');

const certStack = new CertificateStack(app, 'JobbetCertificateStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'us-east-1' },
  crossRegionReferences: true,
  hostname,
  hostedZoneDomain,
});

const appStack = new AppStack(app, 'JobbetAppStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-north-1' },
  crossRegionReferences: true,
  certificate: certStack.certificate,
  hostname,
  hostedZoneDomain,
});

appStack.addDependency(certStack);
