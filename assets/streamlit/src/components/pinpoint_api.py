"""
Helper classes for Amazon Pinpoint
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

## ********* Pinpoint API ********* 
def invoke_pinpoint_segment( 
    access_token: str,
) -> list:
    """
    Get Segments From Pinpoint Project
    """
    response = requests.get(
        url=API_URI + "/pinpoint/segment",
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_pinpoint_create_export_job(
    access_token: str,
    segment_id: str
) -> list:
    """
    Create Export Job For A Pinpoint Segment
    """
    params = {
        "segment-id": segment_id
    }
    response = requests.post(
        url=API_URI + "/pinpoint/job",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_pinpoint_export_job_status(
    access_token: str,
    job_id: str
) -> list:
    """
    Get Export Job Status From Pinpoint
    """
    params = {
        "job-id": job_id
    }
    response = requests.get(
        url=API_URI + "/pinpoint/job",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_pinpoint_send_message(
    access_token: str,
    address: str,
    channel: str,
    message_body_text: str,
    message_subject: str = None,
    message_body_html: str = None
) -> list:
    """
    Send Message via Pinpoint
    """
    params = {
        "address": address,
        "channel": channel,
        "message-subject": message_subject,
        "message-body-html": message_body_html,
        "message-body-text": message_body_text,
    }
    response = requests.post(
        url=API_URI + "/pinpoint/message",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

def invoke_s3_fetch_files(
    access_token: str,
    s3_url_prefix: str,
    total_pieces: int,
) -> list:
    """
    Get Files URI from S3 which were exported by Pinpoint
    """
    params = {
        "s3-url-prefix": s3_url_prefix,
        "total-pieces": total_pieces,
    }
    response = requests.get(
        url=API_URI + "/s3",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
    )
    return response.content

