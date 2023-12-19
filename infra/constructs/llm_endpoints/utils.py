from sagemaker.utils import sagemaker_timestamp

from infra.constructs.llm_endpoints.constants import NAME_SEPARATOR

MAX_RESOURCE_NAME_LENGTH = 63


def create_resource_name(base_name: str) -> str:
    ts = sagemaker_timestamp()
    max_base_length = MAX_RESOURCE_NAME_LENGTH - len(ts) - 1
    return NAME_SEPARATOR.join([base_name[:max_base_length], ts])
