import boto3
import datetime
import json
import shutil
import subprocess
import os
import logging
import pathlib
import sqlmodel
import sys
import typing as t
import yaml
from jupyter_book.cli.main import build
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import ModuleEnum, IS_DEBUG, DB_URL, DEFAULT_SFS_DIR
from src._common.keys import KeyPath
from src._common.models import (
    Asset,
    File,
    FileService,
    Substitution,
    SubstitutionService,
    Ref,
    RefService,
)
from src._common.state import DocumentState, read_book_metadata
from config_prep import update_with_substitutions
from fakers import Faker
from verif_book import RefsAndTargetsVerifier
from verif_warnings import MessagesJson


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


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = _get_key(event)
    _log_audit_event(key, AuditStatus.PENDING.value, "Building book in progress...")
    _log_tree(key)
    # _mkdir_read()
    _copy_assets(key)
    book_metadata = read_book_metadata(key)
    _prepare_config(key, book_metadata)
    _make_substitutions(key, book_metadata)
    _build_jb1_book(key)
    _distribute_jb1_book(key)

    _build_jb2_book(key)
    _distribute_jb2_book(key)

    _log_tree(key)
    _log_audit_event(key, AuditStatus.SUCCESS.value, "Digital version was created.")
    # NOTE: post-build phase, this should probably go to another Lambda service
    _connect_assets_to_references_to_assets(book_metadata)
    # _write_assets_info_to_s3(book_metadata, key)
    # _write_metadata_to_db(book_metadata, key)
    _update_refs_in_db(book_metadata, key)
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
    print("new_path created", new_path)
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
        dst = key.efs_jb_dir / "_build" / "html" / dirname
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


def _prepare_config(key: KeyPath, book_metadata: dict[str, DocumentState]) -> None:
    if not (key.efs_jb_dir / "_config.yml").exists():
        logging.info(f"{key.efs_jb_dir / '_config.yml'} was not found.")
        return
    with open(key.efs_jb_dir / "_config.yml") as f:
        config = yaml.safe_load(f)
    # TODO: update file_count from values in _config
    config = update_with_substitutions(config, book_metadata)
    with open(key.efs_jb_dir / "_config.yml", "w") as f:
        yaml.dump(config, f)


def _make_substitutions(key: KeyPath, book_metadata: dict[str, DocumentState]) -> None:
    """
    Replace substitution placeholders in markdown files with new values.

    I don't like this implementation because it should be done for .md and .ipynb
    by JupyterBook. Also, I don't like having too many slow IO operations.
    However, I needed some solution fast and I didn't have time to fight with JupyterBook.
    I couldn't make JupyterBook to do the substitutions for f2f refs.
    """
    for md in key.efs_jb_dir.glob("*.md"):
        dstate = book_metadata.get(md.stem)
        try:
            if md.stem not in book_metadata:
                continue
            with open(md, "r") as f:
                mdstr = f.read()
                # Make mapping of file_count to file prefix.
                # This is suboptimal, but FileDatapoint only knows file stem and prefix.
                # I could add more data to it, but since user has to correctly
                # write this data in yaml file by hand, the less data the better :/
                file_prefices: dict[int, str] = {}
                files: list[File] = dstate["files"]
                for file in files:
                    file_count = FileService.get_number_from_filename(file.stem)
                    file_prefices[file_count] = file.prefix
                # Replace placeholders with new values, incl. file prefix
                substitutions: list[Substitution] = dstate["substitutions"]
                for subs in substitutions:
                    if subs.file_count in file_prefices:
                        file_prefix = file_prefices[subs.file_count]
                    else:
                        file_prefix = None
                    mdstr = mdstr.replace(
                        r"{{ " + subs.pk + r" }}",
                        SubstitutionService.to_digital_version(subs, file_prefix),
                    )
                    # NOTE: seems to just repeat "was" attr
            # post_mdstr = mdstr
            # if pre_mdstr != post_mdstr:
            #     diff = difflib.ndiff(
            #         pre_mdstr.splitlines(keepends=True),
            #         post_mdstr.splitlines(keepends=True),
            #     )
            #     print("".join(diff), end="")
            with open(md, "w") as f:
                f.write(mdstr)
        except Exception as e:
            logger.exception(f"Replacing placeholders in {md} failed. Error: {repr(e)}")
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Error upon updating automatic numbering.",
            )


def _log_tree(key: KeyPath) -> None:
    """
    Log the directory tree of the book.
    """
    try:
        flist = [str(f) for f in key.efs_jb_dir.rglob("*")]
        logger.info(f"Files in dir {key.efs_jb_dir}:\n{flist}")
    except Exception as e:
        logger.exception(f"Logging directory tree failed. Error: {repr(e)}")


def _build_jb1_book(key: KeyPath) -> None:
    try:
        logger.info(f"key.efs_slug_dir: {str(key.efs_jb_dir)}")
        logger.info(
            f"Files in {str(key.efs_jb_dir)}: {str(os.listdir(key.efs_jb_dir))}"
        )
        if not (key.efs_jb_dir / "_config.yml").exists():
            logging.info(
                f"{key.efs_jb_dir / '_config.yml'} was not found. Skipping build."
            )
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Invalid configuration. Operation aborted.",
            )
            return
        if not (key.efs_jb_dir / "_toc.yml").exists():
            logging.info(
                f"{key.efs_jb_dir / '_toc.yml'} was not found. Skipping build."
            )
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Invalid table of contents. Operation aborted.",
            )
            return
        params = {
            "path_source": key.efs_jb_dir,
            "path_output": key.efs_jb_dir,
            "config": key.efs_jb_dir / "_config.yml",
            "toc": key.efs_jb_dir / "_toc.yml",
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
        logging.info(f"Builder finished building the JBv1 book at {key.efs_jb_dir}.")
    except RuntimeError as e:
        logging.exception(f"Unable to build JBv1 book. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Runtime error while Jupyter Book v1 build operation.",
        )
    except Exception as e:
        logging.exception(f"Unable to build JBv1 book. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while Jupyter Book v1 build operation.",
        )
        raise


# def _build_verification_report(key: KeyPath) -> None:
#     return
#     if not (key.efs_slug_dir / "_config.yml").exists():
#         logging.info(
#             f"{key.efs_slug_dir / '_config.yml'} was not found. Skipping build."
#         )
#         return
#     if not (key.efs_slug_dir / "_toc.yml").exists():
#         logging.info(f"{key.efs_slug_dir / '_toc.yml'} was not found. Skipping build.")
#         return
#     src = key.efs_slug_dir
#     dst = key.efs_slug_dir / "_warnings"
#     shutil.copyfile(src / "_config.yml", dst / "_config.yml")
#     shutil.copyfile(src / "_toc.yml", dst / "_toc.yml")
#     #####################
#     with open(key.efs_slug_dir / "_toc.yml") as f:
#         config = yaml.safe_load(f)
#     chapters = config.get("chapters", [])
#     for i, chapter in enumerate(chapters):
#         if chapter.get("file"):
#             # rewriting "file" key causes infinite loop
#             chapters.insert(i + 1, {"newFile": "refs_" + chapter["file"]})
#     for chapter in chapters:
#         if chapter.get("newFile"):
#             chapter.update({"file": chapter["newFile"]})
#             del chapter["newFile"]
#     with open(key.efs_slug_dir / "_toc.yml", "w") as f:
#         yaml.dump(config, f)
#     #####################
#     try:
#         params = {
#             "path_source": dst,
#             "path_output": dst,
#             "config": dst / "_config.yml",
#             "toc": dst / "_toc.yml",
#             "warningiserror": False,
#             "nitpick": False,
#             "keep_going": False,
#             "freshenv": False,
#             "builder": "html",
#             "custom_builder": None,
#             "verbose": 0,
#             "quiet": 0,
#             "individualpages": False,
#         }
#         if IS_DEBUG:
#             # params["nitpick"] = True
#             params["keep_going"] = True
#             # not sure, but it seems verbose can have levels ranging from 0 to 2
#             # https://github.com/sphinx-doc/sphinx/blob/4fbd3682d5cdf606159630f7daf6f818d58de05e/tests/test_util/test_util_logging.py#L56
#             # params["verbose"] = 2
#         build.callback(**params)
#         logging.info(f"Builder finished building the verification report at {dst}.")
#     except RuntimeError as e:
#         logging.exception(f"Unable to build verification report. Error: {repr(e)}")
#     except Exception as e:
#         logging.exception(f"Unable to build verification report. Error: {repr(e)}")
#         raise


def _distribute_jb1_book(key: KeyPath) -> None:
    src = key.efs_jb_dir / "_build" / "html"
    try:
        if IS_DEBUG:
            _cp_efs_to_data_dir(src, "output", key.slug)
        else:
            _sync_efs_to_staticws(src, "read", key.slug)
    except Exception as e:
        msg = f"Failed to distribute JBv1 book build. Error: {repr(e)}"
        logging.exception(msg)
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while updating the digital version (JBv1).",
        )
        raise


def _build_jb2_book(key: KeyPath) -> None:
    try:
        pass
        # NOTE: Use mystmd pip wrapper. It seems that there won't be any conflicts
        # with Jupyter Book v1. However, check if your docker base image supports it.
        # I tried this, works on my local machine, but not in the docker container.
        # In docker container, myst command is not recognized, even when
        # mystmd==1.6.0 was installed.
        WORKS_IF_YOU_HAVE_MYST_CMD = """subprocess.run(
            f"myst build --html".split(), shell=True, cwd=key.efs_slug_dir
        )"""
    except Exception as e:
        msg = f"Unable to build JBv2 book. Error: {repr(e)}"
        logging.exception(msg)
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while Jupyter Book v2 build operation.",
        )
        raise


def _distribute_jb2_book(key: KeyPath) -> None:
    try:
        pass

        ## Attempt 1: Github Pages
        # probably just send sqs message with new status to github microservice to:
        # 1. call github api to create Github Pages site
        # https://docs.github.com/en/rest/pages/pages?apiVersion=2022-11-28#create-a-github-pages-site
        # 2. (maybe) call github api to update information about the site
        # https://docs.github.com/en/rest/pages/pages?apiVersion=2022-11-28#update-information-about-a-github-pages-site
        # Problem:
        # - With github api, you have to send every file separately. With Jupyter Book v2,
        #   that's around 3500 files for every change. Before upload, you have to download
        #   every file already in the repo, get the sha256 hash of the file, and then
        #   upload the file with the sha256 hash. For. Every. File.

        ## Attempt 2: Netlify
        # Netlify accepts zip uploads, so you can just zip the book and upload it.
        # Try it.

    except Exception as e:
        msg = f"Failed to distribute JBv2 book build. Error: {repr(e)}"
        logging.exception(msg)
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while updating the digital version (JBv2).",
        )
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
    bucket = os.environ.get("STATICWS_WIP_BUCKET_NAME", "")
    dst = f"s3://{bucket}/{dstdir}/{slug}"
    cmd = ["aws", "s3", "sync", "--quiet", src, dst]
    logging.info(f"Syncing files from {src} to {dst}.")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()


def _connect_assets_to_references_to_assets(
    book_metadata: dict[str, DocumentState],
) -> None:
    """
    Find asset id for each reference to asset in the book.
    Assign assets' primary keys to references.
    Note that this updates the "asset_id" field locally. This change
    has to be written to the database later.
    """
    # internal_links: list[RefDatapoint] = []
    for _, dstate in book_metadata.items():
        assets: list[Asset] = dstate["assets"]
        refs: list[Ref] = dstate["refs"]
        for ref in refs:
            href = ref.href
            if RefService.is_internal_infile(href) or RefService.is_internal_f2f(href):
                try:
                    asset = next(ass for ass in assets if ass.target == ref.target_id)
                    ref.asset_id = asset.pk
                    ref._was_updated = True
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


def _update_refs_in_db(book_metadata: dict[str, DocumentState], key: KeyPath) -> None:
    """
    Builder microservice is the aggregating function. Only it sees all the
    documents that compose a book. Only in this microservice we can get information
    about the state of the book from all the documents. Because of that, we can
    use this information to link references to assets and update the db accordingly.

    Fields that can change:
    * asset_id - from None to uuid of the target asset
      (see _connect_assets_to_references_to_assets)
    """
    try:
        with sqlmodel.Session(db_engine) as session:
            for dstate in book_metadata.values():
                # Get all changed references
                changed_refs: list[Ref] = []
                refs_pk: list[int] = []
                for ref in dstate["refs"]:
                    ref: Ref
                    if ref._was_updated:
                        changed_refs.append(ref)
                        refs_pk.append(ref.pk)
                # Select all references that need to be updated
                current_refs = session.exec(
                    sqlmodel.select(Ref).where(sqlmodel.col(Ref.pk).in_(refs_pk))
                ).all()
                # Update every ref that needs to be updated
                for curr_ref in current_refs:
                    curr_ref.asset_id = next(
                        (r.asset_id for r in changed_refs if r.pk == curr_ref.pk), None
                    )
                    session.add(curr_ref)
            session.commit()
    except Exception as e:
        logger.exception(f"Writing metadata to database failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing metadata to database.",
        )
        raise


def _verify_book(
    book_metadata: dict[KeyPath, DocumentState],
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
            bucket = os.environ.get("VERIFIER_MSGS", "")
            resp = s3.put_object(Body=body, Bucket=bucket, Key=str(s3_key))
            logger.info(
                f"Response from s3.put_object(Bucket={bucket}, Key={str(s3_key)}): "
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
