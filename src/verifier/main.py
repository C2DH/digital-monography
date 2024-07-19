import bs4
import boto3
import datetime
import json
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
    from make_warnings_report import make_warnings_report
except ModuleNotFoundError as e:
    from src.verifier.constants import (
        IS_DEBUG,
        VERIFIER_MSGS,
    )
    from src.verifier.html_verifier import HtmlVerifier
    from src.verifier.fakers import Faker
    from src.verifier.keys import KeyPath
    from src.verifier.make_warnings_report import make_warnings_report


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


if IS_DEBUG:
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    key = _get_key(event)
    timestamp = _get_timestamp(event)
    if key.suffix.lower() == ".html":
        if not key.efs_slug_html_path.parent.exists():
            key.efs_slug_html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(key.efs_slug_html_path.with_suffix(".html"), "r") as f:
            html = f.read()
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
        _write_json_to_efs(warnings_json, key)
        _make_warnings_report(verifer.soup, warnings_json, timestamp, key)
        _put_json_to_s3(json.dumps(warnings_json, default=str), key)
        logger.info(f"Time to _send_msg_to_sqs(key).")
        _send_msg_to_sqs(key)
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


def _write_json_to_efs(json_data: t.Any, key: KeyPath) -> None:
    try:
        fp = key.add_to_efs_slug_dir("_warnings").parent / key.github_path.with_suffix(
            ".json"
        )
        with open(fp, "w") as f:
            json.dump(json_data, f)
        logger.info(f"Warnings raw data was saved to {str(fp)}")
    except Exception as e:
        logger.exception(f"Writing json to /efs directory failed. Error: {repr(e)}")
        raise


def _make_warnings_report(
    soup: bs4.BeautifulSoup,
    json_data: t.Any,
    timestamp: datetime.datetime,
    key: KeyPath,
) -> None:
    try:
        fp = key.add_to_efs_slug_dir("_warnings").parent / key.github_path.with_suffix(
            ".md"
        )
        file_name = str(key.with_suffix(".docx").name)
        with open(fp, "w") as f:
            f.write(make_warnings_report(soup, json_data, timestamp, file_name))
        logger.info(f"Warnings markdown report was saved to {str(fp)}")
    except Exception as e:
        logger.exception(f"Writing json to /efs directory failed. Error: {repr(e)}")
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


def _get_queue_url():
    region = "eu-west-1"
    account_id = "367031255351"
    queue_name = "cpy-dgtmon-dev-builder-trigger.fifo"
    return f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"


def _send_msg_to_sqs(key: KeyPath) -> None:
    logger.info(f"Preparing to send a message to the sqs queue.")
    try:
        QueueUrl = "https://sqs.eu-west-1.amazonaws.com/367031255351/cpy-dgtmon-dev-builder-trigger.fifo"
        MessageBody = key.slug
        MessageDeduplicationId = key.slug
        MessageGroupId = "0"
        resp = sqs.send_message(
            QueueUrl=QueueUrl,
            MessageBody=MessageBody,
            MessageDeduplicationId=MessageDeduplicationId,
            MessageGroupId=MessageGroupId,
        )
        logger.info(
            f"Response from sqs.send_message(QueueUrl={QueueUrl}, MessageBody={MessageBody}, MessageDeduplicationId={MessageDeduplicationId}, MessageGroupId={MessageGroupId}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Sending a message to sqs queue failed. Error: {repr(e)}")
        raise
