import base64
import boto3
import json
import logging
from mypy_boto3_s3.client import S3Client as boto3_S3Client

try:
    from constants import (
        APKG_UPLOAD_BUCKET_NAME,
        BE_PATH_ASSET_METADATA,
        # BE_PATH_ASSET_UPLOAD, # NOTE: for upload let "entrypoint" just send ListObjects req
        BE_PATH_ASSET_RETRIEVE,
        BE_PATH_REF_METADATA,
        METADATA_ASSETS_BUCKET_NAME,
        METADATA_REFS_BUCKET_NAME,
        VERIFIER_MSGS,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (  # type: ignore
        APKG_UPLOAD_BUCKET_NAME,
        BE_PATH_ASSET_METADATA,
        # BE_PATH_ASSET_UPLOAD,
        BE_PATH_ASSET_RETRIEVE,
        BE_PATH_REF_METADATA,
        METADATA_ASSETS_BUCKET_NAME,
        METADATA_REFS_BUCKET_NAME,
        VERIFIER_MSGS,
    )

logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3: boto3_S3Client = boto3.client("s3")


def lambda_handler(event, context):
    encoded_key = event["queryStringParameters"]["key"]
    one_day_in_seconds = 86_400
    bucket = _get_s3_bucket_name(event["queryStringParameters"]["type"])
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


def _get_s3_bucket_name(keyword: str) -> str:
    return {
        "asset": APKG_UPLOAD_BUCKET_NAME,
        "assets": METADATA_ASSETS_BUCKET_NAME,
        BE_PATH_ASSET_METADATA: METADATA_ASSETS_BUCKET_NAME,
        BE_PATH_ASSET_RETRIEVE: APKG_UPLOAD_BUCKET_NAME,
        BE_PATH_REF_METADATA: METADATA_REFS_BUCKET_NAME,
        "warnings": VERIFIER_MSGS,
    }[keyword]
