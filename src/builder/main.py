import boto3
import logging
import os
import time
import typing as t
import urllib.parse

# s3 = boto3.client("s3")
try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False
DESTINATION_BUCKET = "dgtmon-dev-staticws-wip"

logger = logging.getLogger(__name__)


def timestamp():
    return int(round(time.time() * 1000))


def get_aws_client(service: str) -> t.Any:
    if IS_LOCAL:
        return boto3.client(
            service,
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="eu-central-1",
            endpoint_url="http://localhost:4566",
        )
    else:
        return boto3.client(service)


def get_s3_client():
    return get_aws_client("s3")


s3 = get_s3_client()


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    key = _get_key(event)
    body = _get_object(event, key)
    _put_object(body, key)
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> str:
    try:
        return urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_object(event, key: str) -> bytes:
    try:
        src = event["Records"][0]["s3"]["bucket"]["name"]
        logger.info(f"Proceeding to get an object {key} from bucket {src}.")
        resp = s3.get_object(Bucket=src, Key=key)
        return resp["Body"].read()
    except Exception as e:
        logger.error(f"Error getting object {key} from bucket {src}. Error: {repr(e)}")
        raise


def _put_object(body: bytes, key: str) -> t.Any:
    try:
        dst = DESTINATION_BUCKET
        return s3.put_object(Body=body.decode("utf-8"), Bucket=dst, Key=key)
    except Exception as e:
        logger.error(f"Put object {key} to bucket {dst} failed. Error: {repr(e)}")
        raise
