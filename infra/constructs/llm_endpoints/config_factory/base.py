
from abc import ABC, abstractmethod
from typing import Any, Dict

from infra.constructs.llm_endpoints.constants import NAME_SEPARATOR
from infra.constructs.llm_endpoints.utils import create_resource_name


class BaseEndpointConfigurationFactory(ABC):

    def __init__(self, user_config: Dict[str, Any], resource_prefix: str) -> None:
        self.user_config = user_config
        self.prefix = resource_prefix

    @abstractmethod
    def create_container_definition_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_model_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_production_variant_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_endpoint_config_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_endpoint_config(self) -> Dict[str, Any]:
        pass


class BasicEndpointConfigurationFactory(BaseEndpointConfigurationFactory):
    
    def create_container_definition_config(self) -> Dict[str, Any]:
        config = {"mode": "SingleModel"}
        if "env" in self.user_config:
            config.update({"environment": self.user_config["env"]})
        return config
    
    def create_model_config(self) -> Dict[str, Any]:
        return  {
            "model_name": create_resource_name(base_name=NAME_SEPARATOR.join([self.prefix, "model"])),
        }

    def create_production_variant_config(self) -> Dict[str, Any]:
        config = {
            "variant_name": "AllTraffic",
            "initial_instance_count": 1,
            "initial_variant_weight": 1.0,
            }
        pv_config_names = ["volume_size_in_gb", "model_data_download_timeout_in_seconds", "container_startup_health_check_timeout_in_seconds", "instance_type"]
        user_config = {key: self.user_config[key] for key in pv_config_names if key in self.user_config}
        config.update(user_config)
        return config
    
    def create_endpoint_config_config(self) -> Dict[str, Any]:
        return {
            "endpoint_config_name": create_resource_name(base_name=NAME_SEPARATOR.join([self.prefix, "endpoint", "config"])),
        }
    
    def create_endpoint_config(self) -> Dict[str, Any]:
        return {
            "endpoint_name": create_resource_name(base_name=NAME_SEPARATOR.join([self.prefix, "endpoint"])),
        }


class NonProprietaryModelEndpointConfigurationFactory(BasicEndpointConfigurationFactory):

    def create_container_definition_config(self) -> Dict[str, Any]:
        config = super().create_container_definition_config()
        if "model_data_url" in self.user_config:
            config.update({"model_data_url": self.user_config["model_data_url"]})
        if "image_uri" in self.user_config:
            config.update({"image": self.user_config["image_uri"]})
        return config
