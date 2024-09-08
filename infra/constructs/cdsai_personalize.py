"""
CDSGenAI Personalize constructs
"""

from typing import Any, Dict

from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_personalize as personalize,
    CfnOutput as output,
)
from constructs import Construct

from cdk_nag import NagSuppressions

import json

interactions_schema_json = {
    "type": "record",
    "name": "Interactions",
    "namespace": "com.amazonaws.personalize.schema",
    "fields": [
        {"name": "ITEM_ID", "type": "string"},
        {"name": "USER_ID", "type": "string"},
        {"name": "TIMESTAMP", "type": "long"},
        {"name": "CABIN_TYPE", "type": "string", "categorical": True},
        {"name": "EVENT_TYPE", "type": "string"},
        {"name": "EVENT_VALUE", "type": "float"},
    ],
    "version": "1.0",
}

users_schema_json = {
    "type": "record",
    "name": "Users",
    "namespace": "com.amazonaws.personalize.schema",
    "fields": [
        {"name": "USER_ID", "type": "string"},
        {"name": "memberClass", "type": "string", "categorical": True},
    ],
    "version": "1.0",
}

items_schema_json = {
    "type": "record",
    "name": "Items",
    "namespace": "com.amazonaws.personalize.schema",
    "fields": [
        {"name": "ITEM_ID", "type": "string"},
        {"name": "DSTCity", "type": ["null", "string"], "categorical": True},
        {"name": "SRCCity", "type": ["null", "string"], "categorical": True},
        {"name": "Airline", "type": ["null", "string"], "categorical": True},
        {"name": "DurationDays", "type": "int"},
        {"name": "Season", "type": ["null", "string"], "categorical": True},
        {"name": "numberOfSearchByUser", "type": "int"},
        # {"name": "Promotion", "type": ["null", "string"], "categorical": True},
        {"name": "DynamicPrice", "type": "int"},
        {"name": "DiscountForMember", "type": "float"},
        {"name": "Expired", "type": ["null", "string"], "categorical": True},
    ],
    "version": "1.0",
}


class PersonalizeConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name: str,
        s3_data_bucket: s3.Bucket,
        deploy_personalize: bool,
        personalize_solution_version_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.personalize_role_ARN = self.grant_personalize_s3_export(s3_data_bucket)
        if deploy_personalize:
            # Deploy infrastructure for personalize
            self.import_datasets(s3_data_bucket)

    def grant_personalize_s3_export(self, bucket):
        # Define the IAM policy
        export_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="PersonalizeS3BucketAccessPolicy",
                    actions=["s3:GetObject", "s3:ListBucket", "s3:PutObject"],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:s3:::{bucket.bucket_name}", f"arn:aws:s3:::{bucket.bucket_name}/*"],
                )
            ]
        )

        # Create the IAM policy
        personalize_policy = iam.ManagedPolicy(self, "PersonalizeS3BucketAccessPolicy", document=export_policy_document)

        NagSuppressions.add_resource_suppressions(
            personalize_policy,
            [{"id": "AwsSolutions-IAM5", "reason": "Policy for Personalize service so wildcards are acceptable"}],
        )

        # Create the IAM Role for Amazon Personalize
        personalize_role = iam.Role(
            self, "PersonalizeS3AccessRole", assumed_by=iam.ServicePrincipal("personalize.amazonaws.com")
        )

        # Attach the policy to the role
        personalize_role.add_managed_policy(personalize_policy)

        return personalize_role.role_arn

    def import_datasets(self, bucket):
        """
        Create dataset import jobs for Personalize
        """

        # Create the dataset group first
        dataset_group = personalize.CfnDatasetGroup(
            self,
            id="AirlinesDatasetGroup",
            name="AirlinesDatasetGroup",
        )

        # Create the datasets
        ## Interactions Dataset
        interactions_schema = personalize.CfnSchema(
            self,
            id="InteractionsSchema",
            name="InteractionsSchema",
            schema=json.dumps(interactions_schema_json),
        )
        interactions_dataset = personalize.CfnDataset(
            self,
            id="InteractionsDataset",
            dataset_group_arn=dataset_group.attr_dataset_group_arn,
            dataset_type="Interactions",
            name="InteractionsDataset",
            schema_arn=interactions_schema.attr_schema_arn,
        )

        ## Users Dataset
        users_schema = personalize.CfnSchema(
            self,
            id="UsersSchema",
            name="UsersSchema",
            schema=json.dumps(users_schema_json),
        )
        users_dataset = personalize.CfnDataset(
            self,
            id="UsersDataset",
            dataset_group_arn=dataset_group.attr_dataset_group_arn,
            dataset_type="Users",
            name="UsersDataset",
            schema_arn=users_schema.attr_schema_arn,
        )

        ## Items Dataset
        items_schema = personalize.CfnSchema(
            self,
            id="ItemsSchema",
            name="ItemsSchema",
            schema=json.dumps(items_schema_json),
        )
        items_dataset = personalize.CfnDataset(
            self,
            id="ItemsDataset",
            dataset_group_arn=dataset_group.attr_dataset_group_arn,
            dataset_type="Items",
            name="ItemsDataset",
            schema_arn=items_schema.attr_schema_arn,
        )
