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
    logger.info(f"Event: {json.dumps(event, default=str)}")
    key = "guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png"
    # key = event["queryStringParameters"]["key"]
    # logger.info("key" + key)
    one_day_in_seconds = 86_400
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": APKG_UPLOAD_BUCKET_NAME, "Key": key},
        ExpiresIn=one_day_in_seconds,
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"presigned_url": presigned_url}),
        "headers": {"Content-Type": "application/json"},
    }
