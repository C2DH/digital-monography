# NOTE : this is not as much builder, as
# book level preparer (preparer works per document)
import boto3
import datetime
import json
import logging
import os
import pathlib
import sqlmodel
import sys
import shutil
import typing as t
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client


# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import ASSETS_DIR, DB_URL, IS_DEBUG, ModuleEnum
from src._common.keys import KeyPath
from src._common.state import BookState
from fakers import Faker

# from src._common.models import File
# from src._common.state import DocumentState, read_book_metadata


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_builder.log")
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
    dynamodb = None  # TODO: add fakers
    s3 = Faker("s3")
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")
db_engine = sqlmodel.create_engine(DB_URL)


def lambda_handler(event, context) -> None:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = _get_key(event)
    _log_audit_event(key, AuditStatus.PENDING.value, "Building book has started.")
    _copy_assets(key)
    _copy_manuscript(key)
    bookstate = _load_book_state(key)
    # make substitutions
    # build book <== no
    # distribute book <== no
    _log_audit_event(key, AuditStatus.SUCCESS.value, "Building book in progress...")
    # connect assets to refs_to_assets
    # update refs in db
    # verify book
    # save warnings
    logging.info("Builder Lambda function finished.")
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        slug = event["Records"][0]["body"]
        pth = pathlib.Path(slug) / "_config.yml"
        return KeyPath(pth)
    except Exception as e:
        logging.exception(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _copy_assets(key: KeyPath) -> None:
    try:
        src = key.efs_slug_dir / ASSETS_DIR
        dst = key.efs_jb_dir / ASSETS_DIR
        dst.mkdir(parents=True, exist_ok=True)
        logging.info(f"Copying files from {src} to {dst}.")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        # cmd = ["cp", "-r", src, dst]
        # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p.wait()
    except Exception as e:
        logging.exception(f"Unable to copy assets. Error: {repr(e)}")
        _log_audit_event(key, AuditStatus.FAILED.value, "Error while copying assets.")
        raise


def _copy_manuscript(key: KeyPath) -> None:
    for md in key.efs_slug_dir.glob("**/*.md"):
        _copy_file_to_jb_dir(md)
    for ipynb in key.efs_slug_dir.glob("**/*.ipynb"):
        _copy_file_to_jb_dir(ipynb)


def _copy_file_to_jb_dir(src: KeyPath) -> None:
    try:
        relative_path = src.relative_to(src.efs_slug_dir)
        dst = src.efs_jb_dir / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        logger.info(f"Copied {src} to {dst}.")
    except Exception as e:
        logger.exception(f"Unable to copy file {src} to {dst}. Error: {repr(e)}")
        _log_audit_event(
            src, AuditStatus.FAILED.value, f"Error while copying chapter {src}."
        )
        raise


def _load_book_state(key: KeyPath) -> BookState:
    try:
        bookstate = BookState()
        bookstate.load_from_file(key)
        bookstate.merge_docstate(key)
        return bookstate
    except Exception as e:
        logging.exception(f"Loading book state failed. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while loading book state."
        )
        raise


RESTORE_FOR_SAVING_WARNINGS = """
def _put_json_to_s3(key: KeyPath, warnings: list[dict[str, str]]) -> None:
    try:
        warnings_grouped: dict[str, list[dict[str, str]]] = {}
        for w in warnings:
            if w.get("fn") not in warnings_grouped:
                warnings_grouped[w.get("fn")] = []
            warnings_grouped[w.get("fn")].append(w)

        for fn, warnings in warnings_grouped.items():
            s3_key = key.slug + "/" + fn.split(".")[0] + ".json"
            body = json.dumps(warnings, default=str)
            bucket = os.environ.get("VERIFIER_MSGS", "")
            resp = s3.put_object(Body=body, Bucket=bucket, Key=str(s3_key))
            logger.info(
                f"Response from s3.put_object(Bucket={bucket}, Key={str(s3_key)}): "
                + json.dumps(resp, default=str)
            )
    except Exception as e:
        logger.exception(f"Putting json to s3 bucket failed. Error: {repr(e)}")
        raise
"""


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.BUILDER.value,
        filename="",
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.FAILED.value:
        alert = AlertLog(slug=key.slug, status=AlertStatus.FAIL.value)
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")
