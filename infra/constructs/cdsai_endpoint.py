from typing import Any, Dict

from aws_cdk import aws_iam as iam
from aws_cdk import aws_sagemaker as sm
from constructs import Construct

from infra.constructs.llm_endpoints.config_factory import (
    BaseEndpointConfigurationFactory,
    HuggingFaceTGIEndpointConfigurationFactory,
    JumpStartEndpointConfigurationFactory,
    MarketplaceModelEndpointConfigurationFactory,
)
from infra.constructs.llm_endpoints.iam import (
    ImageRepositoryAccessGrantor,
    ModelArtifactsAccessGrantor,
    SageMakerEndpointBasicExecutionRole,
)
from infra.constructs.llm_endpoints.constants import NAME_SEPARATOR


class CDSAIEndpointConstructs(Construct):
    ALLOWED_INVOKE_ACTIONS = [
        "sagemaker:InvokeEndpoint",
    ]

    def __init__(self, scope: Construct, construct_id: str, stack_name: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.region_name = scope.region

        execution_role = SageMakerEndpointBasicExecutionRole(
            scope=self, construct_id="EndpointExecutionRole", resource_prefix=stack_name
        )
        endpoint_config_factory = self.create_endpoint_config_factory(config=config, resource_prefix=stack_name)

        container_def_config = endpoint_config_factory.create_container_definition_config()
        sm_container_def = sm.CfnModel.ContainerDefinitionProperty(
            **container_def_config,
        )

        sm_model = sm.CfnModel(
            scope=self,
            id="SageMakerModel",
            primary_container=sm_container_def,
            execution_role_arn=execution_role.arn,
            **endpoint_config_factory.create_model_config(),
        )

        if "model_data_url" in container_def_config:
            model_artifacts_access_grantor = ModelArtifactsAccessGrantor.from_uri(
                scope=self,
                construct_id="ModelArtifactsAccessGrantor",
                resource_prefix=stack_name,
                uri=container_def_config["model_data_url"],
            )
            model_artifacts_access_grantor.grant_read(role=execution_role.role)
            sm_model.node.add_dependency(model_artifacts_access_grantor)

        if "image" in container_def_config:
            image_repository_access_grantor = ImageRepositoryAccessGrantor.from_uri(
                scope=self,
                construct_id="InferenceImageRepositoryAccessGrantor",
                resource_prefix=stack_name,
                uri=container_def_config["image"],
            )
            image_repository_access_grantor.grant_pull(role=execution_role.role)
            sm_model.node.add_dependency(image_repository_access_grantor)

        production_variant = sm.CfnEndpointConfig.ProductionVariantProperty(
            model_name=sm_model.model_name,
            **endpoint_config_factory.create_production_variant_config(),
        )

        sm_endpoint_config = sm.CfnEndpointConfig(
            scope=self,
            id="SageMakerEndpointConfig",
            production_variants=[production_variant],
            **endpoint_config_factory.create_endpoint_config_config(),
        )
        sm_endpoint_config.add_dependency(target=sm_model)

        self.endpoint = sm.CfnEndpoint(
            scope=self,
            id="SageMakerEndpoint",
            endpoint_config_name=sm_endpoint_config.endpoint_config_name,
            **endpoint_config_factory.create_endpoint_config(),
        )
        self.endpoint.add_dependency(target=sm_endpoint_config)

        self._invoke_policy = iam.Policy(
            scope=self,
            id="InvokeEndpointPolicy",
            statements=[
                iam.PolicyStatement(actions=self.ALLOWED_INVOKE_ACTIONS, effect=iam.Effect.ALLOW, resources=[self.arn]),
            ],
            policy_name=NAME_SEPARATOR.join([stack_name, "endpoint", "invocation", "policy"]),
        )

    @property
    def name(self) -> str:
        return self.endpoint.endpoint_name

    @property
    def arn(self) -> str:
        return self.endpoint.ref

    def grant_invoke(self, role: iam.IRole) -> None:
        role.attach_inline_policy(policy=self._invoke_policy)

    def create_endpoint_config_factory(
        self, config: Dict[str, Any], resource_prefix: str
    ) -> BaseEndpointConfigurationFactory:
        "Factory method"
        endpoint_type = config["type"]
        user_config = config.get("endpoint_config", {})
        if endpoint_type == "jumpstart":
            config_factory = JumpStartEndpointConfigurationFactory(
                model_id=config["model_id"],
                model_version=config["model_version"],
                region_name=self.region_name,
                user_config=user_config,
                resource_prefix=resource_prefix,
            )
        elif endpoint_type == "tgi":
            config_factory = HuggingFaceTGIEndpointConfigurationFactory(
                model_id=config["model_id"],
                region_name=self.region_name,
                user_config=user_config,
                resource_prefix=resource_prefix,
            )
        elif endpoint_type == "marketplace":
            config_factory = MarketplaceModelEndpointConfigurationFactory(
                model_package_arn=config["model_package_arn"],
                user_config=user_config,
                resource_prefix=resource_prefix,
            )
        else:
            supported_endpoint_types = ", ".join(["jumpstart", "tgi", "marketplace"])
            raise ValueError(f"Unknown endpoint type: {endpoint_type}. Supported types are: {supported_endpoint_types}")
        return config_factory
