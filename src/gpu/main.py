import base64
import boto3
import json
import logging
import os
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)


try:
    from constants import (
        BE_PATH_ASSET_METADATA,
        BE_PATH_ASSET_RETRIEVE,
        BE_PATH_REF_METADATA,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (  # type: ignore
        BE_PATH_ASSET_METADATA,
        BE_PATH_ASSET_RETRIEVE,
        BE_PATH_REF_METADATA,
    )

logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3: boto3_S3Client = boto3.client("s3")


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context: LambdaContext):
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
        "asset": os.environ.get("APKG_UPLOAD_BUCKET_NAME", ""),
        "assets": os.environ.get("METADATA_ASSETS_BUCKET_NAME", ""),
        BE_PATH_ASSET_METADATA: os.environ.get("METADATA_ASSETS_BUCKET_NAME", ""),
        BE_PATH_ASSET_RETRIEVE: os.environ.get("APKG_UPLOAD_BUCKET_NAME", ""),
        BE_PATH_REF_METADATA: os.environ.get("METADATA_REFS_BUCKET_NAME", ""),
        "warnings": os.environ.get("VERIFIER_DOC_MSGS", ""),
    }[keyword]
