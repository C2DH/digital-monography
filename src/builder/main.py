import boto3
import json
import logging
import os
import typing as t
import urllib.parse

try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False
STATICWS_WIP_BUCKET_NAME = "dgtmon-dev-staticws-wip"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_aws_client(service: str) -> t.Any:
    if IS_LOCAL:
        return boto3.client(
            service,
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="eu-central-1",
            endpoint_url="http://localhost:4566",
        )  # type: ignore
    else:
        return boto3.client(service)  # type: ignore


s3 = get_aws_client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Builder Lambda function was successfully invoked.")
    key = _get_key(event)
    body = _get_object(event, key)
    _put_object(body, key)
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> str:
    try:
        key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        logger.info(f"Key {key} was found in the event records.")
        return key
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_object(event, key: str) -> bytes:
    try:
        src = event["Records"][0]["s3"]["bucket"]["name"]
        logger.info(f"Proceeding to get an object {key} from bucket {src}.")
        resp = s3.get_object(Bucket=src, Key=key)
        logger.info(
            f"Response from s3.get_object(Bucket={src}, Key={key}): "
            + json.dumps(resp, default=str)
        )
        return resp["Body"].read()
    except Exception as e:
        logger.error(f"Error getting object {key} from bucket {src}. Error: {repr(e)}")
        raise


def _put_object(body: bytes, key: str) -> t.Any:
    try:
        dst = STATICWS_WIP_BUCKET_NAME
        if key.endswith(".html"):
            resp = s3.put_object(
                Body=body.decode("utf-8"), Bucket=dst, Key=key, ContentType="text/html"
            )
        else:
            resp = s3.put_object(Body=body.decode("utf-8"), Bucket=dst, Key=key)
        logger.info(
            f"Response from s3.put_object(Bucket={dst}, Key={key}): "
            + json.dumps(resp, default=str)
        )
        return resp
    except Exception as e:
        logger.error(f"Put object {key} to bucket {dst} failed. Error: {repr(e)}")
        raise
