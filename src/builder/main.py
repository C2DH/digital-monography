import boto3
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

from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_dynamodb.client import DynamoDBClient as boto3_DynamoDBClient

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if not IS_DEBUG:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

try:
    from audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from constants import (
        ModuleEnum,
        IS_DEBUG,
        DEFAULT_SFS_DIR,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_WARNINGS_TBL,
        DYNAMODB_REFS_TBL,
        STATICWS_WIP_BUCKET_NAME,
        METADATA_REFS_BUCKET_NAME,
        VERIFIER_MSGS,
    )
    from metadata import (
        DocumentMetadata,
        AssetDatapoint,
        SubstitutionDatapoint,
        RefDatapoint,
        TargetDatapoint,
    )
    from fakers import Faker
    from keys import KeyPath
    from verif_book import RefsAndTargetsVerifier
    from verif_warnings import MessagesJson
except (ImportError, ModuleNotFoundError):
    from .audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from .constants import (
        ModuleEnum,
        IS_DEBUG,
        DEFAULT_SFS_DIR,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_WARNINGS_TBL,
        DYNAMODB_REFS_TBL,
        STATICWS_WIP_BUCKET_NAME,
        METADATA_REFS_BUCKET_NAME,
        VERIFIER_MSGS,
    )
    from .metadata import (
        DocumentMetadata,
        AssetDatapoint,
        SubstitutionDatapoint,
        RefDatapoint,
        TargetDatapoint,
    )
    from .fakers import Faker
    from .keys import KeyPath
    from .verif_book import RefsAndTargetsVerifier
    from .verif_warnings import MessagesJson


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
    dynamodb: boto3_DynamoDBClient = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = _get_key(event)
    _log_audit_event(key, AuditStatus.PENDING.value, "Building book in progress...")
    _mkdir_read()
    _copy_assets(key)
    _prepare_config(key)
    _build_book(key)
    _distribute_book(key)
    _log_audit_event(key, AuditStatus.SUCCESS.value, "Digital version was created.")
    # NOTE: post-build phase, this should probably go to another Lambda service
    book_metadata = _read_book_metadata(key)
    _connect_assets_to_references_to_assets(book_metadata)
    # _write_assets_info_to_s3(book_metadata, key)
    _write_metadata_to_db(book_metadata, key)
    #
    warnings = _verify_book(book_metadata)
    _put_json_to_s3(key, warnings)
    # _write_warnings_to_db(warnings)
    # _build_verification_report(key)
    # _distribute_report(key)
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


# TODO: Check if this is necessary. If not, remove.
def _mkdir_read():
    new_path = pathlib.Path(DEFAULT_SFS_DIR) / "read"
    if not new_path.exists():
        new_path.mkdir(exist_ok=True)


# def merge_jsons(path, key: str):
#     result = []
#     for fp in path.glob("**/*.json"):
#         with open(fp, "r") as infile:
#             records = json.load(infile)
#             result.extend(records[key])
#     with open("new_file.json", "w") as f:
#         json.dump(result, f)


def _copy_assets(key: KeyPath) -> None:
    try:
        # for dirname in SUPPORTED_ASSET_DIR:
        dirname = "assets"
        src = key.efs_slug_dir / dirname
        dst = key.efs_slug_dir / "_build" / "html" / dirname
        logger.info(f"copy assets from {str(src)} to {str(dst)}")
        if dst.exists():
            logger.info(f"BEFORE COPY - assets in {str(dst)}: {str(os.listdir(dst))}")
        if src.exists():
            logger.info(f"BEFORE COPY - assets in {str(src)}: {str(os.listdir(src))}")
            shutil.copytree(src, dst, dirs_exist_ok=True)
            logger.info(f"AFTER COPY - assets in {str(src)}: {str(os.listdir(src))}")
    except Exception as e:
        logging.exception(f"Unable to copy assets. Error: {repr(e)}")
        _log_audit_event(key, AuditStatus.FAILED.value, "Error while copying assets.")
        raise


def _prepare_config(key: KeyPath) -> None:
    if not (key.efs_slug_dir / "_config.yml").exists():
        logging.info(f"{key.efs_slug_dir / '_config.yml'} was not found.")
        return
    with open(key.efs_slug_dir / "_config.yml") as f:
        config = yaml.safe_load(f)

    metadatas = {}
    for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
        meta_file: KeyPath
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            try:
                metadata.from_json(json.load(f))
                metadatas[meta_file.stem] = metadata
            except KeyError as e:
                logger.info(
                    f"Invalid or obsolete DataPoint structure. Skipping "
                    f"metadata file {meta_file}. KeyError: {repr(e)}"
                )
    THIS_IS_HOW_WE_CAN_ACHIEVE_COUNTING_FIGURES_ETC = """
    # ROMAN_NUMS = {
    #     "1": "I",
    #     "2": "II",
    # }
    # IS_ROMAN_NUM = False
    # IS_SEQUENTIAL_NUM = True
    # SEP = "."
    # _substitutions = {
    #     "f01aref177042490": ("1", "1", "fig"),
    #     "f01aref177044323": ("1", "1", "tbl"),
    #     "f02bref177053481": ("2", "1", "fig"),
    #     "f02bref177053494": ("2", "1", "tbl"),
    #     "02bdocxf02btblsimpletable": ("2", "", "tbl"),
    # }
    # _items_count = {"fig": 0, "tbl": 0}
    # substitutions = {}
    # i = 1
    # for k, v in _substitutions.items():
    #     chapter_no, item_no, item_type = v
    #     if IS_SEQUENTIAL_NUM:
    #         # substitutions[k] = str(i)
    #         _items_count[item_type] += 1
    #         substitutions[k] = _items_count[item_type]
    #     elif item_no and not IS_SEQUENTIAL_NUM:
    #         if IS_ROMAN_NUM:
    #             substitutions[k] = ROMAN_NUMS[chapter_no] + SEP + item_no
    #         else:
    #             substitutions[k] = chapter_no + SEP + item_no
    #     else:
    #         substitutions[k] = ""
    #     i += 1
    """
    substitutions = {}
    for metadata in metadatas.values():
        metadata: DocumentMetadata
        # TODO:
        # file_no = _get_file_number(metadata.filepath.stem)
        file_no = metadata.get_chapter_number()
        for dp in metadata.substitutions:
            dp: SubstitutionDatapoint
            if not dp.was.isdigit() and not _is_roman_numeral(dp.was):
                pass
            elif dp.was and not file_no:
                substitutions[dp.placeholder] = dp.was
            elif dp.was:
                substitutions[dp.placeholder] = str(file_no) + "." + dp.was
    try:
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    except KeyError:
        if "sphinx" not in config:
            config["sphinx"] = {}
        if "config" not in config["sphinx"]:
            config["sphinx"]["config"] = {}
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    with open(key.efs_slug_dir / "_config.yml", "w") as f:
        yaml.dump(config, f)


def _is_roman_numeral(was: str) -> bool:
    roman_num_chars = ["I", "V", "X", "L", "C", "D", "M"]
    if not was:
        return False
    for ch in was:
        if ch not in roman_num_chars:
            return False
    return True


def _build_book(key: KeyPath) -> None:
    try:
        logger.info(f"key.efs_slug_dir: {str(key.efs_slug_dir)}")
        logger.info(
            f"Files in {str(key.efs_slug_dir)}: {str(os.listdir(key.efs_slug_dir))}"
        )
        if not (key.efs_slug_dir / "_config.yml").exists():
            logging.info(
                f"{key.efs_slug_dir / '_config.yml'} was not found. Skipping build."
            )
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Invalid configuration. Operation aborted.",
            )
            return
        if not (key.efs_slug_dir / "_toc.yml").exists():
            logging.info(
                f"{key.efs_slug_dir / '_toc.yml'} was not found. Skipping build."
            )
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Invalid table of contents. Operation aborted.",
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
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Runtime error while Jupyter Book build operation.",
        )
    except Exception as e:
        logging.exception(f"Unable to build book. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while Jupyter Book build operation."
        )
        raise


def _build_verification_report(key: KeyPath) -> None:
    return
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
    #####################
    with open(key.efs_slug_dir / "_toc.yml") as f:
        config = yaml.safe_load(f)
    chapters = config.get("chapters", [])
    for i, chapter in enumerate(chapters):
        if chapter.get("file"):
            # rewriting "file" key causes infinite loop
            chapters.insert(i + 1, {"newFile": "refs_" + chapter["file"]})
    for chapter in chapters:
        if chapter.get("newFile"):
            chapter.update({"file": chapter["newFile"]})
            del chapter["newFile"]
    with open(key.efs_slug_dir / "_toc.yml", "w") as f:
        yaml.dump(config, f)
    #####################
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
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while updating the digital version."
        )
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


def _read_book_metadata(key: KeyPath) -> dict[str, DocumentMetadata]:
    """
    Read JSON metadata stored in Elastic File System (EFS) and return a dict
    with all DocumentMetadata objects for a specific book.
    """
    book_metadata: dict[str, DocumentMetadata] = {}
    for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
        meta_file: KeyPath
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            try:
                metadata.from_json(json.load(f))
                book_metadata[meta_file.stem] = metadata
            except KeyError as e:
                logger.info(
                    f"Invalid or obsolete DataPoint structure. Skipping "
                    f"metadata file {meta_file}. KeyError: {repr(e)}"
                )
    return book_metadata


def _connect_assets_to_references_to_assets(
    book_metadata: dict[str, DocumentMetadata],
) -> None:
    """
    Find asset id for each reference to asset in the book.
    Assign assets' primary keys to references.
    """
    # internal_links: list[RefDatapoint] = []
    for _, meta in book_metadata.items():
        for ref in meta.refs:
            ref: RefDatapoint
            if ref.is_internal_infile() or ref.is_internal_f2f():
                try:
                    asset = next(
                        ass for ass in meta.assets if ass.target == ref.target_id
                    )
                    ref.asset_id = asset.pk
                except StopIteration:
                    continue

        # internal_links.extend(
        #     [
        #         ref
        #         for ref in meta.refs
        #         if ref.is_internal_infile() or ref.is_internal_f2f()
        #     ]
        # )
    # for fn, meta in book_metadata.items():
    #     fn: str
    #     logger.info(f"fn: {fn} type: {type(fn)}")
    #     for asset in meta.assets:
    #         asset: AssetDatapoint
    #         if asset.target:
    #             asset.refs = [r for r in internal_links if r.target_id == asset.target]


def _write_metadata_to_db(
    book_metadata: dict[str, DocumentMetadata], key: KeyPath
) -> None:
    if dynamodb is None:
        return
    try:
        tables = {
            "refs": DYNAMODB_REFS_TBL,
        }
        for domain, tbl in tables.items():
            table = dynamodb.Table(tbl)
            for _, metadata in book_metadata.items():
                resp = table.put_item(
                    Item={
                        "slug": key.slug,
                        "fn": metadata.filepath.name,
                        "records": [rec.to_json() for rec in getattr(metadata, domain)],
                    }
                )
                logger.info(
                    f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
                )
        return
    except Exception as e:
        logger.exception(f"Writing metadata to database failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing metadata to database.",
        )
        raise


def _write_assets_info_to_s3(
    book_metadata: dict[str, DocumentMetadata], key: KeyPath
) -> None:
    for fn, metadata in book_metadata.items():
        fn: str
        try:
            s3_key = RefDatapoint.get_s3_key(key.slug, fn)
            bucket = METADATA_REFS_BUCKET_NAME
            body = json.dumps([ref.to_json() for ref in metadata.refs], default=str)
            resp = s3.put_object(Body=body, Bucket=bucket, Key=s3_key)
            logger.info(
                f"Response from s3.put_object(Bucket={bucket}, Key={s3_key}): "
                + json.dumps(resp, default=str)
            )
        except Exception as e:
            logger.exception(f"Putting refs info to s3 bucket failed. Error: {repr(e)}")
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Error upon writing assets info from docs.",
            )
            raise


def _verify_book(
    book_metadata: dict[KeyPath, DocumentMetadata],
) -> list[dict[str, str]]:
    # TODO: stop repeating metadata parsing after _prepare_config()
    # the only difference is just stem str vs pathlib path
    #
    # TODO: move making targets to other place (e.g. metadata???)
    MAYBE_WE_CAN_COMPUTE_TARGETS_BEFOREHAND = """
    targets: dict[str, tuple[pathlib.PurePath, TargetDatapoint]] = {}
    for fn, meta in metadatas.items():
        fn: pathlib.PurePath
        # TODO: check if KeyPath, if yes change from PurePath to KeyPath
        logger.info(f"fn: {fn} type: {type(fn)}")
        for target in meta.targets:
            target: TargetDatapoint
            targets[target.pk] = (fn, target)
    """

    verifier = RefsAndTargetsVerifier()
    return verifier.verify(book_metadata)
    # verifer = BookVerifier()
    # verifer.verify(key, timestamp)
    # verifer.sort()
    # return verifer.to_json(md=True)


def _write_warnings_to_db(warnings: MessagesJson) -> None:
    # TODO: implement
    pass


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
            resp = s3.put_object(Body=body, Bucket=VERIFIER_MSGS, Key=str(s3_key))
            logger.info(
                f"Response from s3.put_object(Bucket={VERIFIER_MSGS}, Key={str(s3_key)}): "
                + json.dumps(resp, default=str)
            )
    except Exception as e:
        logger.exception(f"Putting json to s3 bucket failed. Error: {repr(e)}")
        raise


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
