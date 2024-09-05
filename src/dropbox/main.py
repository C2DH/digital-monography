import base64
import boto3
import datetime
import dropbox
import json
import markdown
import pathlib
import logging
import typing as t


try:
    from constants import (
        APKG_UPLOAD_BUCKET_NAME,
        DYNAMODB_TOKENS_TBL,
        DYNAMODB_CURSORS_TBL,
        IS_DEBUG,
    )
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .constants import (
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
    # token = redis_client.hget("tokens", account)
    logger.info('Here was: `token = redis_client.hget("tokens", account)`')
    tokens_resp = dynamodb_get(DYNAMODB_TOKENS_TBL, {"account": account})
    logger.info("tokens_resp == " + json.dumps(tokens_resp, default=str))
    token = tokens_resp.get("Item", {}).get("access_token")
    logger.info(f"token == {token}")
    # token = TOKEN

    # cursor for the user (None the first time)
    # cursor = redis_client.hget("cursors", account)
    logger.info('Here was: `redis_client.hget("cursors", account)`')
    cursors_resp = dynamodb_get(DYNAMODB_CURSORS_TBL, {"account": account})
    cursor = cursors_resp.get("Item", {}).get("cursor")

    dbx = dropbox.Dropbox(token)
    has_more = True

    while has_more:
        if cursor is None:
            result = dbx.files_list_folder(path="")
        else:
            result = dbx.files_list_folder_continue(cursor)

        for entry in result.entries:
            logger.info("dir(entry)" + json.dumps(dir(entry), default=str))
            logger.info(f"entry.name {entry.name}")
            logger.info(f"entry.path_lower {entry.path_lower}")

            # Ignore deleted files, folders, and non-markdown files
            if (
                isinstance(entry, dropbox.files.DeletedMetadata)
                or isinstance(entry, dropbox.files.FolderMetadata)
                or not entry.path_lower.endswith(".md")
            ):
                continue

            # Convert to Markdown and store as <basename>.html
            metadata, resp = dbx.files_download(entry.path_lower)


            logger.info("dir(metadata)" + json.dumps(dir(metadata), default=str))
            logger.info(f"resp from dbx.files_download {json.dumps(resp.json(), default=str)}")
            logger.info(f'Response content {resp.content.decode("utf-8")}')


            logger.info(f"entry.path_lower: {entry.path_lower}")
            key = KeyPath(entry.path_lower)
            logger.info(f"keypath: {key}")
            logger.info(f"type(resp.content): {type(resp.content)}")
            _put_file_from_dbx_to_s3(resp.content, key)


            html = markdown.markdown(resp.content.decode("utf-8"))
            logger.info("html == " + html)
            dbx.files_upload(
                bytes(html, encoding="utf-8"),
                entry.path_lower[:-3] + ".html",
                mode=dropbox.files.WriteMode("overwrite"),
            )
            logger.info(f"New file '{entry.path_lower[:-3] + '.html'}' was uploaded.")

        # Update cursor
        cursor = result.cursor
        # redis_client.hset("cursors", account, cursor)
        logger.info('Here was: `redis_client.hset("cursors", account, cursor)`')
        dynamodb_set(DYNAMODB_CURSORS_TBL, **{"account": account, "cursor": cursor})

        # Repeat only if there's more to do
        has_more = result.has_more
        logger.info("result.has_more loop in process_user has ended.")
    logger.info("process_user has ended.")
    return {"statusCode": 200, "body": ""}


def dynamodb_set(tbl: str, **kwargs) -> None:
    expire_at = int((datetime.datetime.now() + datetime.timedelta(days=3)).timestamp())
    table = dynamodb.Table(tbl)
    logger.info(f"{json.dumps({"expire_at": expire_at, **kwargs}, default=str)}")
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
        # _put_object(
        #     contents.encode("utf-8"),
        #     IR_APKG_HTML_BUCKET_NAME,
        #     s3_key,
        # )
    except Exception as e:
        logger.exception(f"Putting file from Dropbox to {dst} bucket failed. Error: {repr(e)}")
        raise
