import datetime
import json
import shutil
import subprocess
import os
import logging
import pathlib
import sys
import typing as t
import yaml
from jupyter_book.cli.main import build

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if not IS_DEBUG:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

try:
    from keys import KeyPath
    from constants import IS_DEBUG, DEFAULT_SFS_DIR, STATICWS_WIP_BUCKET_NAME
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath
    from .constants import (
        IS_DEBUG,
        DEFAULT_SFS_DIR,
        STATICWS_WIP_BUCKET_NAME,
    )


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
    _prepare_config(key)
    _build_book(key)
    _distribute_book(key)
    # this should probably go to another Lambda service
    _build_verification_report(key)
    _distribute_report(key)
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


def _prepare_config(key: KeyPath) -> None:
    if not (key.efs_slug_dir / "_config.yml").exists():
        logging.info(
            f"{key.efs_slug_dir / '_config.yml'} was not found. Skipping build."
        )
        return
    with open(key.efs_slug_dir / "_config.yml") as f:
        config = yaml.safe_load(f)
    ROMAN_NUMS = {
        "1": "I",
        "2": "II",
    }
    IS_ROMAN_NUM = False
    IS_SEQUENTIAL_NUM = True
    SEP = "."
    _substitutions = {
        "f01aref177042490": ("1", "1", "fig"),
        "f01aref177044323": ("1", "1", "tbl"),
        "f02bref177053481": ("2", "1", "fig"),
        "f02bref177053494": ("2", "1", "tbl"),
        "02bdocxf02btblsimpletable": ("2", "", "tbl"),
    }
    _items_count = {"fig": 0, "tbl": 0}
    substitutions = {}
    i = 1
    for k, v in _substitutions.items():
        chapter_no, item_no, item_type = v
        if IS_SEQUENTIAL_NUM:
            # substitutions[k] = str(i)
            _items_count[item_type] += 1
            substitutions[k] = _items_count[item_type]
        elif item_no and not IS_SEQUENTIAL_NUM:
            if IS_ROMAN_NUM:
                substitutions[k] = ROMAN_NUMS[chapter_no] + SEP + item_no
            else:
                substitutions[k] = chapter_no + SEP + item_no
        else:
            substitutions[k] = ""
        i += 1
    config["sphinx"]["config"]["myst_substitutions"] = substitutions
    with open(key.efs_slug_dir / "_config.yml", "w") as f:
        yaml.dump(config, f)


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
            # params["nitpick"] = True
            params["keep_going"] = True
            # not sure, but it seems verbose can have levels ranging from 0 to 2
            # https://github.com/sphinx-doc/sphinx/blob/4fbd3682d5cdf606159630f7daf6f818d58de05e/tests/test_util/test_util_logging.py#L56
            # params["verbose"] = 2
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
            # params["nitpick"] = True
            params["keep_going"] = True
            # not sure, but it seems verbose can have levels ranging from 0 to 2
            # https://github.com/sphinx-doc/sphinx/blob/4fbd3682d5cdf606159630f7daf6f818d58de05e/tests/test_util/test_util_logging.py#L56
            # params["verbose"] = 2
        build.callback(**params)
        logging.info(f"Builder finished building the verification report at {dst}.")
    except RuntimeError as e:
        logging.exception(f"Unable to build verification report. Error: {repr(e)}")
    except Exception as e:
        logging.exception(f"Unable to build verification report. Error: {repr(e)}")
        raise


def _distribute_book(key: KeyPath) -> None:
    src = key.efs_slug_dir / "_build" / "html"
    try:
        if IS_DEBUG:
            _cp_efs_to_data_dir(src, "output", key.slug)
        else:
            _sync_efs_to_staticws(src, "read", key.slug)
    except Exception as e:
        msg = f"Failed to copy post-build warnings report. Error: {repr(e)}"
        logging.exception(msg)
        raise


def _distribute_report(key: KeyPath) -> None:
    try:
        src = key.efs_slug_dir / "_warnings" / "_build" / "html"
        if IS_DEBUG:
            _cp_efs_to_data_dir(src, "warnings", key.slug)
        else:
            _sync_efs_to_staticws(src, "check", key.slug)
    except Exception as e:
        msg = f"Failed to copy post-build warnings report. Error: {repr(e)}"
        logging.exception(msg)
        raise


def _cp_efs_to_data_dir(src: pathlib.Path, dstdir: str, slug: str) -> None:
    if os.environ.get("DGTMON_VOLUME") is None:
        msg = f"Files were not copied to {dstdir} as there is no DGTMON_VOLUME environment variable."
        logging.info(msg)
        return
    dst = pathlib.Path(os.environ.get("DGTMON_VOLUME")) / dstdir / slug
    if not dst.exists():
        dst.mkdir(exist_ok=True)
    logging.info(f"Copying files from {src} to {dst}.")
    shutil.copytree(src, dst, symlinks=False, ignore=None, dirs_exist_ok=True)


def _sync_efs_to_staticws(src: pathlib.Path, dstdir: str, slug: str) -> None:
    src = str(src)
    dst = f"s3://{STATICWS_WIP_BUCKET_NAME}/{dstdir}/{slug}"
    cmd = ["aws", "s3", "sync", "--quiet", src, dst]
    logging.info(f"Syncing files from {src} to {dst}.")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
