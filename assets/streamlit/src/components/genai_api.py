"""
Helper classes for LLM inference
"""

#########################
#    IMPORTS & LOGGER
#########################

from __future__ import annotations

import json
import os

import requests

#########################
#      CONSTANTS
#########################

API_URI = os.environ.get("API_URI")


#########################
#    HELPER FUNCTIONS
#########################


def invoke_content_creation(
    prompt: str,
    model_id: int,
    access_token: str,
    answer_length: int = 4096,
    temperature: float = 0.0,
) -> str:
    """
    Run LLM to generate content via API
    """

    params = {
        "query": prompt,
        "type": "content_generation",
        "model_params": {
            "model_id": model_id,
            "answer_length": answer_length,
            "temperature": temperature,
        },
    }
    response = requests.post(
        url=API_URI + "/content/bedrock",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    print(response.text)
    response = json.loads(response.text)
    return response
