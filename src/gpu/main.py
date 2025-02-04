import base64
import boto3
import json
import logging

try:
    from constants import (
        APKG_UPLOAD_BUCKET_NAME,
        METADATA_ASSETS_BUCKET_NAME,
        VERIFIER_MSGS,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        APKG_UPLOAD_BUCKET_NAME,
        METADATA_ASSETS_BUCKET_NAME,
        VERIFIER_MSGS,
    )

logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")


def lambda_handler(event, context):
    typ = event["queryStringParameters"]["type"]
    encoded_key = event["queryStringParameters"]["key"]
    one_day_in_seconds = 86_400
    if typ == "asset":
        bucket = APKG_UPLOAD_BUCKET_NAME
    elif typ == "assets":
        bucket = METADATA_ASSETS_BUCKET_NAME
    elif typ == "warnings":
        bucket = VERIFIER_MSGS
    key = base64.b64decode(encoded_key).decode("utf-8")
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=one_day_in_seconds,
    )
    body = json.dumps({"presigned_url": presigned_url})
    return {
        "statusCode": 200,
        "body": body,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET",
        },
    }
