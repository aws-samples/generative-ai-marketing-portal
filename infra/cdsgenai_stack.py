"""
Marketing Agent Portal Stack
"""

from typing import Any, Dict

from aws_cdk import Aws
from aws_cdk import CfnOutput as output
from aws_cdk import RemovalPolicy, Stack, Tags
from aws_cdk import aws_s3 as _s3

from constructs import Construct

from infra.constructs.cdsai_api import CDSAIAPIConstructs
from infra.constructs.cdsai_endpoint import CDSAIEndpointConstructs
from infra.constructs.cdsai_pinpoint import PinpointConstructs
from infra.constructs.cdsai_personalize import PersonalizeConstruct
from infra.stacks.streamlit import StreamlitStack

sm_endpoints = {}


class CDSGenAIStack(Stack):
    """
    GenAI Marketing Agent Portal Stack
    """

    def __init__(self, scope: Construct, stack_name: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, stack_name, **kwargs)

        ## **************** Create S3 Bucket ****************

        self.bucket_name = f"{stack_name.lower()}-data-{Aws.ACCOUNT_ID}"
        self.s3_data_bucket = _s3.Bucket(
            self,
            id=f"{stack_name}-cdsai-data",
            bucket_name=self.bucket_name,
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_prefix="access-logs/",
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        output(
            self,
            id="S3BucketNameOutput",
            description="S3 Bucket Name for Storing Data",
            value=self.s3_data_bucket.bucket_name,
        )

        ## ********** SageMaker Endpoint Constructs ***********
        if "endpoint" in config:
            self.endpoint_constructs = CDSAIEndpointConstructs(
                scope=self,
                construct_id=f"{stack_name}-ENDPOINT",
                stack_name=stack_name,
                config=config["endpoint"],
            )

        ## ********** Bedrock configs ***********
        bedrock_region = kwargs["env"].region
        bedrock_role_arn = None

        if "bedrock" in config:
            if "region" in config["bedrock"]:
                bedrock_region = (
                    kwargs["env"].region if config["bedrock"]["region"] == "None" else config["bedrock"]["region"]
                )
            if "cross_account" in config["bedrock"]:
                if config["bedrock"]["cross_account"]:
                    bedrock_role_arn = config["bedrock"]["cross_account_role_arn"]

        ## **************** Pinpoint Constructs ****************
        self.pinpoint_constructs = PinpointConstructs(
            self,
            f"{stack_name}-PINPOINT",
            stack_name=stack_name,
            create_project=config["pinpoint"]["create_pinpoint_project"],
            project_id=config["pinpoint"]["existing_pinpoint_project_id"],
            email_identity=config["pinpoint"]["email_identity"],
            sms_identity=config["pinpoint"]["sms_identity"],
            s3_data_bucket=self.s3_data_bucket,
        )

        ## **************** Personalize Constructs ****************
        # If there is no personalize solution version arn, provided then deploys infrastructure for personalize
        self.personalize_constructs = PersonalizeConstruct(
            self,
            f"{stack_name}-PERSONALIZE",
            stack_name=stack_name,
            s3_data_bucket=self.s3_data_bucket,
            deploy_personalize=config["personalize"]["deploy_personalize_infrastructure"],
            personalize_solution_version_arn=config["personalize"]["personalize_solution_version_arn"],
        )

        output(
            self,
            "PersonalizeRoleARN",
            description="Personalize Role ARN",
            value=self.personalize_constructs.personalize_role_ARN,
        )

        ## **************** API Constructs  ****************
        self.api_constructs = CDSAIAPIConstructs(
            self,
            f"{stack_name}-API",
            stack_name=stack_name,
            s3_data_bucket=self.s3_data_bucket,
            bedrock_region=bedrock_region,
            bedrock_role_arn=bedrock_role_arn,
            pinpoint_project_id=self.pinpoint_constructs.pinpoint_project_id,
            pinpoint_export_role_arn=self.pinpoint_constructs.pinpoint_role_ARN,
            architecture=config["lambda"]["architecture"],
            python_runtime=config["lambda"]["python_runtime"],
            email_identity=config["pinpoint"]["email_identity"],
            sms_identity=config["pinpoint"]["sms_identity"],
            personalize_role_arn=self.personalize_constructs.personalize_role_ARN,
            personalize_solution_version_arn=config["personalize"]["personalize_solution_version_arn"],
        )

        output(
            self,
            "APIURI",
            description="API URI",
            value=self.api_constructs.api_uri,
        )
        output(self, "Cognito Client ID", description="Cognito Client ID", value=self.api_constructs.client_id)

        ## **************** Streamlit NestedStack ****************
        if config["streamlit"]["deploy_streamlit"]:
            self.streamlit_constructs = StreamlitStack(
                self,
                f"{stack_name}-STREAMLIT",
                stack_name=stack_name,
                client_id=self.api_constructs.client_id,
                api_uri=self.api_constructs.api_uri,
                ecs_cpu=config["streamlit"]["ecs_cpu"],
                ecs_memory=config["streamlit"]["ecs_memory"],
                cover_image_url=config["streamlit"]["cover_image_url"],
                s3_data_bucket=self.s3_data_bucket,
                cover_image_login_url=config["streamlit"]["cover_image_login_url"],
                open_to_public_internet=config["streamlit"]["open_to_public_internet"],
                ip_address_allowed=config["streamlit"].get("ip_address_allowed"),
                custom_header_name=config["cloudfront"]["custom_header_name"],
                custom_header_value=config["cloudfront"]["custom_header_value"],
            )

            self.cloudfront_distribution_name = output(
                self,
                id="CloudfrontDistributionDomain",
                description="Public URL to access Cloudfront"
                value=self.streamlit_constructs.cloudfront.domain_name,
            )

        ## **************** Tags ****************
        Tags.of(self).add("StackName", stack_name)
        Tags.of(self).add("Team", "GENAIMARKETING")
