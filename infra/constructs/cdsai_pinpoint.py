"""
CDSGenAI Pinpoint Construct
"""

from typing import Any, Dict

from aws_cdk import (
    aws_pinpoint as pinpoint,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_iam as iam,
    aws_ses as ses,
    Aws,
)
from constructs import Construct

from cdk_nag import NagSuppressions


class PinpointConstructs(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name: str,
        create_project: bool,
        project_id: str,
        email_identity: str,
        sms_identity: str,
        s3_data_bucket=s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.pinpoint_project_id = self.create_pinpoint_project(create_project, project_id)
        self.pinpoint_role_ARN = self.grant_pinpoint_s3_export(s3_data_bucket, self.pinpoint_project_id)
        self.deployed_bucket = self.upload_sample_segment_s3(s3_data_bucket)
        self.setup_email_identity(email_identity)
        self.setup_sms_channel()

    def create_pinpoint_project(self, create_project, project_id=None):
        # Initialize Pinpoint Project or get project ID
        if create_project:
            pinpoint_project = pinpoint.CfnApp(self, id="cds-ai-pinpoint", name="cds-ai-pinpoint")
            return pinpoint_project.ref
        else:
            return project_id

    def grant_pinpoint_s3_export(self, bucket, project_id):
        # Define the IAM policy
        export_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="AllowUserToSeeBucketListInTheConsole",
                    actions=["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
                    effect=iam.Effect.ALLOW,
                    resources=["arn:aws:s3:::*"],
                ),
                iam.PolicyStatement(
                    sid="AllowAllS3ActionsInBucket",
                    actions=["s3:*"],
                    effect=iam.Effect.ALLOW,
                    resources=[bucket.bucket_arn, f"{bucket.bucket_arn}/*"],
                ),
            ]
        )

        # Create the IAM policy
        pinpoint_policy = iam.ManagedPolicy(self, "s3ExportPolicy", document=export_policy_document)

        NagSuppressions.add_resource_suppressions(
            pinpoint_policy,
            [{"id": "AwsSolutions-IAM5", "reason": "Policy for Pinpoint service so wildcards are acceptable"}],
        )

        # Define the trust relationship
        trust_relationship = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sts:AssumeRole"],
            principals=[iam.ServicePrincipal("pinpoint.amazonaws.com")],
            conditions={
                "ArnLike": {"aws:SourceArn": f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{project_id}"}
            },
        )

        # Create the IAM role and attach the policy
        pinpoint_role = iam.Role(
            self,
            "s3ExportRole",
            assumed_by=iam.PrincipalWithConditions(
                iam.ServicePrincipal("pinpoint.amazonaws.com"), trust_relationship.conditions
            ),
        )

        pinpoint_role.add_managed_policy(pinpoint_policy)

        return pinpoint_role.role_arn

    def upload_sample_segment_s3(self, bucket):
        # Deploy Sample File onto Buckets
        pinpoint_sample_segment_deployment = s3_deploy.BucketDeployment(
            self,
            "s3_segment_sample_file_deployment",
            destination_bucket=bucket,
            sources=[s3_deploy.Source.asset("./assets/demo-data")],
            destination_key_prefix="demo-data/",
            retain_on_delete=False,
        )

        return pinpoint_sample_segment_deployment.deployed_bucket

    def setup_email_identity(self, email_identity):
        # First verify the email identity with Amazon SES
        identity = ses.EmailIdentity(self, "email_identity", identity=ses.Identity.email(email_identity))

        # Enable Amazon Pinpoint Email Channel

        cfn_email_channel = pinpoint.CfnEmailChannel(
            self,
            "pinpoint_email_channel",
            application_id=self.pinpoint_project_id,
            from_address=email_identity,
            identity=f"arn:aws:ses:{Aws.REGION}:{Aws.ACCOUNT_ID}:identity/{identity.email_identity_name}",
            enabled=True,
        )

        return cfn_email_channel

    def setup_sms_channel(self):
        # Enable Amazon Pinpoint SMS Channel
        cfn_sms_channel = pinpoint.CfnSMSChannel(
            self,
            "pinpoint_sms_channel",
            application_id=self.pinpoint_project_id,
            enabled=True,
        )
        return cfn_sms_channel
