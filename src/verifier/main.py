import json
import boto3
import datetime
import logging
import pathlib
import typing as t
import urllib.parse

try:
    from constants import (
        IS_DEBUG,
        VERIFIER_MSGS,
    )
    from html_verifier import HtmlVerifier
    from fakers import Faker
    from keys import KeyPath

except ModuleNotFoundError as e:
    from src.verifier.constants import (
        IS_DEBUG,
        VERIFIER_MSGS,
    )
    from src.verifier.html_verifier import HtmlVerifier
    from src.verifier.fakers import Faker
    from src.verifier.keys import KeyPath


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)


if IS_DEBUG:
    s3 = Faker("s3")
else:
    s3 = boto3.client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    key = _get_key(event)
    timestamp = _get_timestamp(event)
    if key.suffix.lower() == ".html":
        with open(key.efs_slug_html_path.with_suffix(".html"), "r") as f:
            html = f.read()
        verifer = HtmlVerifier()
        result = verifer.verify(
            html,
            key.efs_slug_html_path.with_suffix(".html"),
            timestamp=timestamp,
        ).to_json()
        logger.info(json.dumps(result, default=str))
        _put_json_to_s3(json.dumps(result, default=str), key)
        return {"statusCode": 200, "body": ""}
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_timestamp(event) -> datetime.datetime:
    try:
        return datetime.datetime.fromtimestamp(event["Records"][0]["eventTime"])
    except Exception as e:
        logger.error(
            f"Unable to retrieve event time. Event: " + json.dumps(event, default=str)
        )
        raise


def _put_json_to_s3(body: str, key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".json")
        resp = s3.put_object(Body=body, Bucket=VERIFIER_MSGS, Key=str(s3_key))
        logger.info(
            f"Response from s3.put_object(Bucket={VERIFIER_MSGS}, Key={str(s3_key)}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Putting json to s3 bucket failed. Error: {repr(e)}")
        raise
