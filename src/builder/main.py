import pathlib
import shutil
import subprocess
import logging
import typing as t
import urllib.parse
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


SUPPORTED_ASSET_DIR = ["assets", "images", "videos"]


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    key = _get_key(event)
    _mkdir_read()
    _copy_assets(key)
    _build_book(key)
    _sync_efs_and_s3_with_staticws(key)
    logging.info("Builder Lambda function finished.")
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logging.exception(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _mkdir_read():
    new_path = pathlib.Path(DEFAULT_SFS_DIR) / "read"
    if not new_path.exists():
        new_path.mkdir(exist_ok=True)


def _copy_assets(key: KeyPath) -> None:
    try:
        for dirname in SUPPORTED_ASSET_DIR:
            src = key.efs_slug_dir / dirname
            dst = key.efs_slug_dir / "_build" / "html" / dirname
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
    except Exception as e:
        logging.exception(f"Unable to copy assets. Error: {repr(e)}")
        raise


def _build_book(key: KeyPath) -> None:
    try:
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
    except Exception as e:
        logging.exception(f"Unable to build book. Error: {repr(e)}")
        raise


def _sync_efs_and_s3_with_staticws(key: KeyPath) -> None:
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
        logging.exception(f"Syncing exception. Error: {repr(e)}")
        raise
