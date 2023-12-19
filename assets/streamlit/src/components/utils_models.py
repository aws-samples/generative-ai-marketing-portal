import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

BEDROCK_MODELS = [
    "Bedrock: Claude V2",
    "Bedrock: Claude Instant",
    "Bedrock: J2 Grande Instruct",
    "Bedrock: J2 Jumbo Instruct",
    "Bedrock: Amazon Titan",
]

FILTER_BEDROCK_MODELS = ["ALL"] + BEDROCK_MODELS


def get_models_specs(sm_endpoints: Dict[str, Dict[str, str]], path: Path) -> Tuple[List[str], Dict[str, Any]]:
    """
    Get list of models displayed in the UI and their specs (i.e. their default parameters)

    Parameters
    ----------
    sm_endpoints : dict
        Dictionary of Sagemaker deployed endpoints configurations.
        Format: {friendly_unique_name:{'endpoint_name':...,'container':...,'model_id':...}}
    path :
        os path

    Returns
    -------
    MODEL_SPECS : dict
        dictionary of default parameters per model
    MODELS_DISPLAYED : list
        list of models displayed
    """

    # default model specs
    with open(f"{path.parent.absolute()}/components/bedrock_model_specs.json") as f:
        model_specs = json.load(f)
    with open(f"{path.parent.absolute()}/components/sm_endpoints_model_specs.json") as f:
        sm_endpoints_model_specs = json.load(f)

    sm_endpoints_friendly_names = list(sm_endpoints.keys())

    sm_endpoints_model_default_config = {
        friendly_name: sm_endpoints_model_specs[model_spec["model_id"]]
        for friendly_name, model_spec in sm_endpoints.items()
    }
    model_specs.update(sm_endpoints_model_default_config)

    # for key, value in sm_endpoints.items():
    #     model_specs[key] = sm_endpoints_model_specs[value["model_id"]]

    models_displayed = BEDROCK_MODELS + sm_endpoints_friendly_names
    return models_displayed, model_specs
