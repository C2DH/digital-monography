import base64
import boto3
import datetime
import dropbox
import json
import pathlib
import dropbox.exceptions
import requests
import logging
import typing as t


try:
    from audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from constants import (
        ModuleEnum,
        APKG_UPLOAD_BUCKET_NAME,
        DYNAMODB_TOKENS_TBL,
        DYNAMODB_CURSORS_TBL,
        IS_DEBUG,
    )
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from .constants import (
        ModuleEnum,
        APKG_UPLOAD_BUCKET_NAME,
        DYNAMODB_TOKENS_TBL,
        DYNAMODB_CURSORS_TBL,
        IS_DEBUG,
    )
    from .keys import KeyPath


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
    # TODO: add fakers
    dynamodb = None
    s3 = None
else:
    dynamodb = boto3.resource("dynamodb")
    s3 = boto3.client("s3")


def lambda_handler(event, context):
    logger.info("Event" + json.dumps(event, default=str))
    logger.info("Context" + json.dumps(context, default=str))
    request_data = json.loads(base64.b64decode(event["Records"][0]["body"]))
    logger.info(f"Message: {request_data}, type={type(request_data)}")

    try:
        request_data["list_folder"]["accounts"]
    except Exception as e:
        return {"statusCode": 200, "body": ""}

    for account in request_data["list_folder"]["accounts"]:
        # We need to respond quickly to the webhook request, so we do the
        # actual work in a separate thread. For more robustness, it's a
        # good idea to add the work to a reliable queue and process the queue
        # in a worker process.
        process_user(account)
    return {"statusCode": 200, "body": ""}


def process_user(account):
    """Call /files/list_folder for the given user ID and process any changes."""
    logger.info("process_user function was invoked with account " + str(account))
    # OAuth token for the user
    tokens_resp = dynamodb_get(DYNAMODB_TOKENS_TBL, {"account": account})
    logger.info("tokens_resp == " + json.dumps(tokens_resp, default=str))
    token = tokens_resp.get("Item", {}).get("access_token")
    logger.info(f"token == {token}")
    # token = TOKEN

    # cursor for the user (None the first time)
    cursors_resp = dynamodb_get(DYNAMODB_CURSORS_TBL, {"account": account})
    cursor = cursors_resp.get("Item", {}).get("cursor")
    msg, slug = "", ""
    filenames = []

    try:
        dbx = dropbox.Dropbox(token)
        has_more = True

        while has_more:
            if cursor is None:
                logger.info(">.> dbx.files_list_folder")
                result = dbx.files_list_folder(path="", recursive=True)
            else:
                logger.info(">.> dbx.files_list_folder_continue")
                result = dbx.files_list_folder_continue(cursor)
            logger.info(f"result.entries {result.entries}")
            if len(result.entries) == 0:
                logger.info(f"result {result}")
            for entry in result.entries:
                logger.info(f"type(entry) {type(entry)}")
                logger.info(f"entry.name {entry.name}")
                logger.info(f"entry.path_lower {entry.path_lower}")
                slug = next(part for part in entry.path_lower.split("/") if part)

                if isinstance(entry, dropbox.files.FolderMetadata):
                    logger.info("Object is a folder.")
                    logger.info(f"{entry}")
                    msg += f"Folder '{entry.name}' detected, no action taken. "
                elif isinstance(entry, dropbox.files.DeletedMetadata):
                    logger.info("Object is a deleted file.")
                    logger.info(f"{entry}")
                    logger.info("For now we don't handle file deletions.")
                    msg += f"System refuses to delete {entry.name}. "
                    # TODO: Call s3.delete_object to remove it.
                    # This will require to implement it across all modules!
                elif isinstance(entry, dropbox.files.FileMetadata):
                    logger.info(f"Object path_lower is {entry.path_lower}.")
                    _download_file(dbx, entry)
                    filenames.append(entry.name)
                    msg += f"The file '{entry.name}' successfully uploaded. "

            # Update cursor
            cursor = result.cursor
            dynamodb_set(DYNAMODB_CURSORS_TBL, **{"account": account, "cursor": cursor})

            # Repeat only if there's more to do
            has_more = result.has_more
            logger.info("result.has_more loop in process_user has ended.")
        logger.info("process_user has ended.")
        if slug and filenames:
            _log_audit_event(slug, AuditStatus.SUCCESS.value, msg, filenames[0])
        elif slug:
            _log_audit_event(slug, AuditStatus.SUCCESS.value, msg)
        return {"statusCode": 200, "body": ""}
    except dropbox.exceptions.AuthError as e:
        # TODO: "Dropbox" str and API Gateway endpoint should not be constant
        _log_audit_event(
            slug,
            AuditStatus.FAILED.value,
            "Access denied. Please log in to Dropbox from 'https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com/test/login'",
        )
        alert = AlertLog(
            slug=slug,
            status=AlertStatus.NOAUTH.value
        )
        alert.send(dynamodb)
        logger.exception("Access denied. Error: " + repr(e))
        return {"statusCode": 401, "body": "dropbox.exceptions.AuthError"}


def dynamodb_set(tbl: str, **kwargs) -> None:
    expire_at = int((datetime.datetime.now() + datetime.timedelta(days=3)).timestamp())
    table = dynamodb.Table(tbl)
    # logger.info(f"{json.dumps({"expire_at": expire_at, **kwargs}, default=str)}")
    resp = table.put_item(Item={"expire_at": expire_at, **kwargs})
    logger.info(
        f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
    )


def dynamodb_get(tbl: str, pk: dict[str, str]) -> dict[str, t.Any]:
    table = dynamodb.Table(tbl)
    resp = table.get_item(Key=pk)
    logger.info(
        f"Response from dynamodb.Table({tbl}).get_item: {json.dumps(resp, default=str)}"
    )
    return resp


def _put_file_from_dbx_to_s3(body: bytes, key: KeyPath) -> None:
    # This lambda cannot save to EFS because it is outside of the VPC
    # To remedy that, I write to S3 and the next Lambda in the pipeline
    # downloads it from there.
    try:
        dst = APKG_UPLOAD_BUCKET_NAME
        resp = s3.put_object(Body=body, Bucket=dst, Key=str(key))
        logger.info(
            f"Response from s3.put_object(Bucket={dst}, Key={key}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(
            f"Putting file from Dropbox to {dst} bucket failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key.slug, AuditStatus.FAILED.value, "Error upon synchronization.", key.name
        )
        alert = AlertLog(
            slug=slug,
            status=AlertStatus.FAIL.value
        )
        alert.send(dynamodb)
        raise


def _download_file(dbx: dropbox.Dropbox, entry: dropbox.files.FileMetadata) -> None:
    logger.info("_download_file")
    meta, resp = dbx.files_download(entry.path_lower)
    meta: dropbox.files.FileMetadata
    resp: requests.models.Response
    logger.info(f"entry.path_lower: {entry.path_lower}")
    p = entry.path_lower[1:] if entry.path_lower[0] == "/" else entry.path_lower
    logger.info(f"path: {p}")
    key = KeyPath(p)
    logger.info(f"keypath: {key}")
    logger.info(f"type(resp.content): {type(resp.content)}")
    _put_file_from_dbx_to_s3(resp.content, key)


def _log_audit_event(slug: str, status: int, msg: str, fn: str = "") -> None:
    if not slug:
        return
    event = AuditEvent(
        slug=slug,
        module=ModuleEnum.DROPBOX.value,
        filename=fn,
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.SUCCESS.value:
        alert = AlertLog(
            slug=slug,
            status=AlertStatus.START.value
        )
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")
