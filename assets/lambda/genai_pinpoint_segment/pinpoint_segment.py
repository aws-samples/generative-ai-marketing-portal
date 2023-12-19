"""
Lambda that fetches interacts with Pinpoint through APIGateway
"""

#########################
#   LIBRARIES & LOGGER
#########################

import json
import logging
import os
import sys
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


LOGGER = logging.Logger("Content-generation", level=logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


#########################
#        HELPER
#########################

PINPOINT_PROJECT_ID = os.environ["PINPOINT_PROJECT_ID"]

#########################
#        HANDLER
#########################


def lambda_handler(event, context):
    # Get the HTTP method from the event object
    http_method = event['requestContext']['http']['method']
    

    # Check if the request is a GET request
    if http_method == 'GET':
        # Get the Pinpoint project ID from the environment variable
        pinpoint_project_id = os.environ['PINPOINT_PROJECT_ID']
        
        # Create a Pinpoint client
        client = boto3.client('pinpoint')

        try:
            # Perform the get-segments operation
            response = client.get_segments(
                ApplicationId=pinpoint_project_id
            )
            
            # Extract the segments
            segments = response['SegmentsResponse']['Item']

            # Return the segments as a JSON response
            return {
                'statusCode': 200,
                'body': json.dumps(segments),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

        except ClientError as e:
            # Handle any errors that occur
            print(e)
            return {
                'statusCode': 500,
                'body': 'An error occurred while fetching the segments',
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
    else:
        # Return an error response for unsupported HTTP methods
        return {
            'statusCode': 400,
            'body': 'Unsupported HTTP method',
            'headers': {
                'Content-Type': 'application/json'
            }
        }