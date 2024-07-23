import boto3
import datetime
import json
import logging
import os
import pathlib
import sys
import typing as t
import urllib.parse


IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if not IS_DEBUG:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_verifier.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    from fakers import Faker
    from keys import KeyPath
    from html_verifier import HtmlVerifier
except ModuleNotFoundError as e:
    from src.verifier.fakers import Faker
    from src.verifier.keys import KeyPath
    from src.verifier.html_verifier import HtmlVerifier


if IS_DEBUG:
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Handler was invoked successfully.")
    key = _get_key(event)
    timestamp = _get_timestamp(event)
    if key.suffix.lower() == ".html":
        if not key.efs_slug_html_path.parent.exists():
            key.efs_slug_html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(key.efs_slug_html_path.with_suffix(".html"), "r") as f:
            html = f.read()
        logger.info(f"key.efs_slug_html_path: {key.efs_slug_html_path}")
        verifer = HtmlVerifier()
        verifer.verify(
            html,
            key.efs_slug_html_path.with_suffix(".html"),
            slug=key.slug,
            timestamp=timestamp,
        )
        verifer.sort()
        warnings_json = verifer.to_json(md=True)
        logger.info(json.dumps(warnings_json, default=str))
    logger.info("Handler ended successfully.")
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


def _fromtimestamp(event_time: str) -> datetime.datetime:
    return datetime.datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S.%f%z")


def _get_timestamp(event) -> datetime.datetime:
    try:
        event_time = event["Records"][0]["eventTime"]
        return _fromtimestamp(event_time)
    except Exception as e:
        logger.error(
            f"Unable to retrieve event time. Event: "
            + json.dumps(event, default=str)
            + ". Exception: "
            + repr(e)
        )
        raise
