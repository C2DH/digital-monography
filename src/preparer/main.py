import boto3
import json
import logging
import os
import typing as t
import urllib.parse

import bs4
import mammoth
from md_extraction import BookMetadata

try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False
# DESTINATION_BUCKET = "dgtmon-dev-ir-apkg-md"
IR_APKG_HTML_BUCKET_NAME = "dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "dgtmon-dev-ir-apkg-md"

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
    logger.info("Preparer Lambda function was successfully invoked.")
    key = _get_key(event)
    src = _get_source_bucket(event)
    try:
        with open(f"/tmp/{key}", "wb") as fileobj:
            resp = s3.download_fileobj(src, key, fileobj)
            logger.info(
                f"Response from s3.download_fileobj(Bucket={src}, Key={key}): "
                + json.dumps(resp, default=str)
            )
            logger.info(f"Fileobj type: {type(fileobj)}")
            logger.info(f"Fileobj: " + json.dumps(fileobj, default=str))
        with open(f"/tmp/{key}", "rb") as f:
            style_mappings = """
            p[style-name='Quote'] => blockquote:fresh
            """
            result = mammoth.convert_to_html(f, style_map=style_mappings)
            logger.info(f"Result.value: {result.value}")
    except Exception as e:
        logger.exception(
            f"Downloading fileobj {key} from {src} failed. Error: {repr(e)}"
        )
        raise

    try:
        html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        logger.info("Html soup: " + str(html_soup))
    except Exception as e:
        logger.exception(f"Creation of bs4.BeautifulSoup failed. Error: {repr(e)}")
        raise

    try:
        metadata = BookMetadata()
        logger.info("BookMetadata object created successfully (did it though?).")
        logger.info(str(metadata))
    except Exception as e:
        logger.exception(f"Creation of bs4.BeautifulSoup failed. Error: {repr(e)}")
        raise

    # body = _get_object(event, key)
    # _put_object(body, IR_APKG_HTML_BUCKET_NAME, key)
    # _put_object(body, IR_APKG_MD_BUCKET_NAME, key)
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


def _get_source_bucket(event) -> str:
    try:
        src = event["Records"][0]["s3"]["bucket"]["name"]
        logger.info(f"Source-bucket {src} was found in the event records.")
        return src
    except Exception as e:
        logger.error(f"Unable to retrieve the source-bucket. Error: {repr(e)}")
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


def _put_object(body: bytes, dst: str, key: str) -> t.Any:
    try:
        # dst = DESTINATION_BUCKET
        resp = s3.put_object(Body=body.decode("utf-8"), Bucket=dst, Key=key)
        logger.info(
            f"Response from s3.put_object(Bucket={dst}, Key={key}): "
            + json.dumps(resp, default=str)
        )
        return resp
    except Exception as e:
        logger.error(f"Put object {key} to bucket {dst} failed. Error: {repr(e)}")
        raise
