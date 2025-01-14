import base64
import boto3
import json
import logging

try:
    from constants import APKG_UPLOAD_BUCKET_NAME
except (ImportError, ModuleNotFoundError):
    from .constants import APKG_UPLOAD_BUCKET_NAME

logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")


def lambda_handler(event, context):
    pk = event["queryStringParameters"]["pk"]
    key = base64.b64decode(pk).decode("utf-8")
    one_day_in_seconds = 86_400
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": APKG_UPLOAD_BUCKET_NAME, "Key": key},
        ExpiresIn=one_day_in_seconds,
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"presigned_url": presigned_url}),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET",
        },
    }
