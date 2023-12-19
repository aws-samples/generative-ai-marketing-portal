"""
Lambda that interacts with Amazon Personalize and S3 through APIGateway
"""

#########################
#   LIBRARIES & LOGGER
#########################

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

import boto3
import tempfile
from botocore.exceptions import ClientError


LOGGER = logging.Logger("Content-generation", level=logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


#########################
#        HELPER
#########################

bucket_name = os.environ["BUCKET_NAME"]
role_arn = os.environ["PERSONALIZE_ROLE_ARN"]
solution_version_arn = os.environ["SOLUTION_VERSION_ARN"]
#########################
#        HANDLER
#########################


def lambda_handler(event, context):
    print(event)
    # Get the HTTP method from the event object
    http_method = event["requestContext"]["http"]["method"]

    # Create personalize client
    personalize = boto3.client(service_name="personalize")

    # Check if the request is a POST request
    if http_method == "POST":
        # parse event
        event = json.loads(event["body"])
        item_ids = event["item-ids"]

        # generate job name
        job_name = str(uuid.uuid4())

        ### Upload input file to s3 with list of itemIDs

        # Split the string by commas to get a list of item IDs
        item_id_list = item_ids.split(",")
        # Create a JSON string with the desired format
        json_string = "\n".join([json.dumps({"itemId": item_id}) for item_id in item_id_list])
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_file.write(json_string)
            temp_file.flush()

            # Upload the file to the specified S3 location
            s3 = boto3.client("s3")
            s3.upload_file(temp_file.name, bucket_name, f"personalize-input/{job_name}.json")

        s3_input = f"s3://{bucket_name}/personalize-input/{job_name}.json"
        s3_output = f"s3://{bucket_name}/personalize-output/{job_name}/"
        num_results = event["num-results"]

        try:
            create_batch_segment_response = personalize.create_batch_segment_job(
                jobName=job_name,
                solutionVersionArn=solution_version_arn,
                numResults=num_results,
                jobInput={"s3DataSource": {"path": s3_input}},
                jobOutput={"s3DataDestination": {"path": s3_output}},
                roleArn=role_arn,
            )

            # Return the batch segment response as a JSON response
            return {
                "statusCode": 200,
                "body": json.dumps(create_batch_segment_response),
                "headers": {"Content-Type": "application/json"},
            }

        except ClientError as e:
            # Handle any errors that occur
            print(e)
            return {
                "statusCode": 500,
                "body": "An error occurred while fetching the segments",
                "headers": {"Content-Type": "application/json"},
            }

    elif http_method == "GET":
        # Extract the job ARN from the event
        event = json.loads(event["body"])
        job_arn = event["job-arn"]
        if not job_arn:
            return {
                "statusCode": 400,
                "body": "job-arn parameter is required for GET request",
                "headers": {"Content-Type": "application/json"},
            }

        try:
            # Call describe-batch-segment-job to get the job details
            response = personalize.describe_batch_segment_job(batchSegmentJobArn=job_arn)
            return {
                "statusCode": 200,
                "body": json.dumps(response, default=datetime_handler),
                "headers": {"Content-Type": "application/json"},
            }

        except ClientError as e:
            # Handle any errors that occur
            print(e)
            return {
                "statusCode": 500,
                "body": "An error occurred while fetching the segment job details",
                "headers": {"Content-Type": "application/json"},
            }

    else:
        # Return an error response for unsupported HTTP methods
        return {"statusCode": 400, "body": "Unsupported HTTP method", "headers": {"Content-Type": "application/json"}}


def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")
