import datetime
import json
import shutil
import subprocess
import logging
import pathlib
import typing as t
from jupyter_book.cli.main import build

try:
    from keys import KeyPath
    from constants import IS_DEBUG, DEFAULT_SFS_DIR, STATICWS_WIP_BUCKET_NAME
except ModuleNotFoundError:
    from src.builder.keys import KeyPath
    from src.builder.constants import (
        IS_DEBUG,
        DEFAULT_SFS_DIR,
        STATICWS_WIP_BUCKET_NAME,
    )


# TODO: this is legacy, only `assets` should be permitted.
# As far as I know, there should be no problem of just limiting
# supported asset dir to `assets`. After DH Wash, try to change it.
# SUPPORTED_ASSET_DIR = ["assets", "images", "videos",]

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


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = _get_key(event)
    _mkdir_read()
    _copy_assets(key)
    _build_book(key)
    _build_verification_report(key)
    _sync_book_efs_with_staticws(key)
    _sync_report_efs_with_staticws(key)
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


def _fromtimestamp(event_time: str) -> datetime.datetime:
    return datetime.datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S.%f%z")


# TODO: Check if this is necessary. If not, remove.
def _mkdir_read():
    new_path = pathlib.Path(DEFAULT_SFS_DIR) / "read"
    if not new_path.exists():
        new_path.mkdir(exist_ok=True)


def _copy_assets(key: KeyPath) -> None:
    try:
        # for dirname in SUPPORTED_ASSET_DIR:
        dirname = "assets"
        src = key.efs_slug_dir / dirname
        dst = key.efs_slug_dir / "_build" / "html" / dirname
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
    except Exception as e:
        logging.exception(f"Unable to copy assets. Error: {repr(e)}")
        raise


def _build_book(key: KeyPath) -> None:
    try:
        if not (key.efs_slug_dir / "_config.yml").exists():
            logging.info(
                f"{key.efs_slug_dir / '_config.yml'} was not found. Skipping build."
            )
            return
        if not (key.efs_slug_dir / "_toc.yml").exists():
            logging.info(
                f"{key.efs_slug_dir / '_toc.yml'} was not found. Skipping build."
            )
            return
        params = {
            "path_source": key.efs_slug_dir,
            "path_output": key.efs_slug_dir,
            "config": key.efs_slug_dir / "_config.yml",
            "toc": key.efs_slug_dir / "_toc.yml",
            "warningiserror": False,
            "nitpick": False,
            "keep_going": False,
            "freshenv": False,
            "builder": "html",
            "custom_builder": None,
            "verbose": 0,
            "quiet": 0,
            "individualpages": False,
        }
        if IS_DEBUG:
            params["nitpick"] = True
            params["keep_going"] = True
            # not sure, but it seems verbose can have levels ranging from 0 to 2
            # https://github.com/sphinx-doc/sphinx/blob/4fbd3682d5cdf606159630f7daf6f818d58de05e/tests/test_util/test_util_logging.py#L56
            params["verbose"] = 2
        build.callback(**params)
        logging.info(f"Builder finished building the book at {key.efs_slug_dir}.")
    except RuntimeError as e:
        logging.exception(f"Unable to build book. Error: {repr(e)}")
    except Exception as e:
        logging.exception(f"Unable to build book. Error: {repr(e)}")
        raise


def _build_verification_report(key: KeyPath) -> None:
    if not (key.efs_slug_dir / "_config.yml").exists():
        logging.info(
            f"{key.efs_slug_dir / '_config.yml'} was not found. Skipping build."
        )
        return
    if not (key.efs_slug_dir / "_toc.yml").exists():
        logging.info(f"{key.efs_slug_dir / '_toc.yml'} was not found. Skipping build.")
        return
    src = key.efs_slug_dir
    dst = key.efs_slug_dir / "_warnings"
    shutil.copyfile(src / "_config.yml", dst / "_config.yml")
    shutil.copyfile(src / "_toc.yml", dst / "_toc.yml")
    try:
        params = {
            "path_source": dst,
            "path_output": dst,
            "config": dst / "_config.yml",
            "toc": dst / "_toc.yml",
            "warningiserror": False,
            "nitpick": False,
            "keep_going": False,
            "freshenv": False,
            "builder": "html",
            "custom_builder": None,
            "verbose": 0,
            "quiet": 0,
            "individualpages": False,
        }
        if IS_DEBUG:
            params["nitpick"] = True
            params["keep_going"] = True
            # not sure, but it seems verbose can have levels ranging from 0 to 2
            # https://github.com/sphinx-doc/sphinx/blob/4fbd3682d5cdf606159630f7daf6f818d58de05e/tests/test_util/test_util_logging.py#L56
            params["verbose"] = 2
        build.callback(**params)
        logging.info(f"Builder finished building the verification report at {dst}.")
    except RuntimeError as e:
        logging.exception(f"Unable to build verification report. Error: {repr(e)}")
    except Exception as e:
        logging.exception(f"Unable to build verification report. Error: {repr(e)}")
        raise


def _sync_book_efs_with_staticws(key: KeyPath) -> None:
    if IS_DEBUG:
        return
    try:
        src = str(key.efs_slug_dir / "_build" / "html")
        dst = f"s3://{STATICWS_WIP_BUCKET_NAME}/read/{key.slug}"
        cmd = ["aws", "s3", "sync", "--quiet", src, dst]
        logging.info(f"Syncing files from {src} to {dst}")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
    except Exception as e:
        logging.exception(
            f"Exception while syncing book efs with static website s3. Error: {repr(e)}"
        )
        raise


def _sync_report_efs_with_staticws(key: KeyPath) -> None:
    if IS_DEBUG:
        return
    try:
        src = str(key.efs_slug_dir / "_warnings" / "_build" / "html")
        dst = f"s3://{STATICWS_WIP_BUCKET_NAME}/check/{key.slug}"
        cmd = ["aws", "s3", "sync", "--quiet", src, dst]
        logging.info(f"Syncing files from {src} to {dst}")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
    except Exception as e:
        logging.exception(
            f"Exception while syncing verification report efs with static website s3. Error: {repr(e)}"
        )
        raise
