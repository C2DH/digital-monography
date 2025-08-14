import boto3
import datetime
import json
import logging
import os
import pathlib
import sys
import typing as t
import urllib.parse
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_sqs import SQSClient as boto3_SQSClient

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import ModuleEnum, S3Event, IS_DEBUG
from src._common.keys import KeyPath
from fakers import Faker
from rules_v1 import HtmlVerifier

# try:
#     from audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
#     from constants import ModuleEnum, S3Event, IS_DEBUG
#     from fakers import Faker
#     from rules_v1 import HtmlVerifier
#     from keys import KeyPath
# except (ImportError, ModuleNotFoundError):
#     from .audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
#     from .constants import ModuleEnum, S3Event, IS_DEBUG
#     from .fakers import Faker
#     from .rules_v1 import HtmlVerifier
#     from .keys import KeyPath

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
    dynamodb = None
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")
    sqs: boto3_SQSClient = boto3.client("sqs")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Handler was invoked successfully.")
    key = _get_key(event)
    event_name = _get_event_name(event)
    timestamp = _get_timestamp(event)
    if key.suffix.lower() == ".html" and event_name == S3Event.OBJ_REMOVED.value:
        pass  # TODO: implement removal of the verification messages
    if key.suffix.lower() == ".html" and event_name == S3Event.OBJ_CREATED.value:
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
        TEMP_DISABLED_FOR_BUILDER_WARNINGS = """
        _write_json_to_efs(warnings_json, key)
        # _make_warnings_report(verifer.soup, warnings_json, timestamp, key)
        _put_json_to_s3(json.dumps(warnings_json, default=str), key)
        """  # TODO: revert
    _send_msg_to_sqs(key)
    logger.info("Handler ended successfully.")
    _log_audit_event(
        key, AuditStatus.SUCCESS.value, "Verification of the file is finished."
    )
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


def _get_event_name(event) -> t.Literal["ObjectCreated", "ObjectRemoved"]:
    try:
        event_name: str = event["Records"][0]["eventName"]
        # event_name should match "event:httpMethod" format, e.g. "ObjectCreated:Put"
        assert ":" in event_name, f"Event name {event_name} is not supported."
        event_name, _ = event_name.split(":")
        assert event_name in (
            "ObjectCreated",
            "ObjectRemoved",
        ), f"Event name {event_name} is not supported."
        return event_name
    except Exception as e:
        logger.error(f"Unable to retrieve event name. Error: {repr(e)}")
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
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Writing verification warnings failed."
        )
        raise


def _put_json_to_s3(body: str, key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".json")
        bucket = os.environ.get("VERIFIER_MSGS", "")
        resp = s3.put_object(Body=body, Bucket=bucket, Key=str(s3_key))
        logger.info(
            f"Response from s3.put_object(Bucket={bucket}, Key={str(s3_key)}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Putting json to s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error upon internal synchronization."
        )
        raise


def _send_msg_to_sqs(key: KeyPath) -> None:
    logger.info(f"Preparing to send a message to the sqs queue.")
    try:
        aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
        aws_account_region = os.environ.get("AWS_ACCOUNT_REGION")
        sqs_builder_trigger = os.environ.get("SQS_BUILDER_FIFO_TRIGGER_NAME")
        QueueUrl = f"https://sqs.{aws_account_region}.amazonaws.com/{aws_account_id}/{sqs_builder_trigger}"
        MessageBody = key.slug
        MessageDeduplicationId = key.slug
        MessageGroupId = "0"
        logger.info(
            f"Attempting to call sqs.send_message(QueueUrl={QueueUrl}, MessageBody={MessageBody}, MessageDeduplicationId={MessageDeduplicationId}, MessageGroupId={MessageGroupId})"
        )
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
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error upon internal synchronization."
        )
        raise


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.VERIFIER.value,
        filename=key.name,
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.FAILED.value:
        alert = AlertLog(slug=key.slug, status=AlertStatus.FAIL.value)
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")


# def _get_character_and_word_count(soup: bs4.BeautifulSoup) -> tuple[int, int]:
#     soup_contents_list = []
#     for elem in soup.find_all(text=True):
#         soup_contents_list.append(elem.text.strip())
#     soup_contents = "".join(soup_contents_list).replace(" ", "")  # minimize spaces
#     words = []
#     for line in soup_contents_list:
#         for word in line.split(" "):
#             if word and not word.isspace():
#                 words.append(word)
#     return len(soup_contents), len(words)
