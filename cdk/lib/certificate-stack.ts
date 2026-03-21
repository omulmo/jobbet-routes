import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';

export interface CertificateStackProps extends cdk.StackProps {
  hostname: string;
  hostedZoneDomain: string;
}

export class CertificateStack extends cdk.Stack {
  public readonly certificate: acm.ICertificate;

  constructor(scope: Construct, id: string, props: CertificateStackProps) {
    super(scope, id, props);

    const hostedZone = route53.HostedZone.fromLookup(this, 'Zone', {
      domainName: props.hostedZoneDomain,
    });

    this.certificate = new acm.Certificate(this, 'Cert', {
      domainName: props.hostname,
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });
  }
}
