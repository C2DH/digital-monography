import pathlib
import shutil
import subprocess
import logging
import typing as t
import urllib.parse
from jupyter_book.cli.main import build

try:
    from keys import KeyPath
    from constants import DEFAULT_SFS_DIR, STATICWS_WIP_BUCKET_NAME
except ModuleNotFoundError:
    from src.builder.keys import KeyPath
    from src.builder.constants import DEFAULT_SFS_DIR, STATICWS_WIP_BUCKET_NAME


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
        build.callback(
            path_source=key.efs_slug_dir,
            path_output=key.efs_slug_dir,
            config=key.efs_slug_dir / "_config.yml",
            toc=key.efs_slug_dir / "_toc.yml",
            warningiserror=False,
            nitpick=False,
            keep_going=False,
            freshenv=False,
            builder="html",
            custom_builder=None,
            verbose=0,
            quiet=0,
            individualpages=False,
        )
        logging.info(f"Builder finished building the book at {key.efs_slug_dir}.")
    except Exception as e:
        logging.exception(f"Unable to build book. Error: {repr(e)}")
        raise


def _sync_efs_and_s3_with_staticws(key: KeyPath) -> None:
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
