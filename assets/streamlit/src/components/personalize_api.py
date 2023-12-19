"""
Helper classes for Amazon Personalize
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

## ********* Personalize API ********* 
def invoke_personalize_batch_segment( 
    access_token: str,
    item_ids: str,
    num_results: int,
) -> list:
    """
    Start batch segmentation job in Personalzie
    """

    params = {
        "item-ids": item_ids,
        "num-results": num_results,
    }
    response = requests.post(
        url=API_URI + "/personalize/batch-segment-job",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_personalize_get_jobs( 
    access_token: str,
) -> list:
    """
    Get all batch segment jobs in personalize
    """

    params = {
    }
    response = requests.get(
        url=API_URI + "/personalize/batch-segment-jobs",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_personalize_describe_job( 
    access_token: str,
    job_arn = str,
) -> list:
    """
    Describe a batch segment job in personalize
    """

    params = {
        "job-arn": job_arn
    }
    response = requests.get(
        url=API_URI + "/personalize/batch-segment-job",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content