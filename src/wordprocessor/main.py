import argparse
import boto3
import datetime
import docx.document
import json
import logging
import os
import pathlib
import sys
import typing as t
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import IS_DEBUG, ModuleEnum
from src._common.keys import KeyPath
from src._common.state import BookState
from numbering_captions import add_chapter_number_to_captions
from numbering_refs import prepare_refs, update_targets_count
from remove_images import remove_images
from wpr_conditional_rendering import (
    remove_parts_and_highlights_due_to_conditional_rendering,
)


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path", type=str)


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_wordprocessor.log")
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
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")


def lambda_handler(event, context) -> None:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    cfg_key = _get_config_key(event)
    bookstate = _load_book_state(cfg_key)
    update_targets_count(bookstate)
    for key in cfg_key.efs_input_dir.glob("*.docx"):
        doc = wordprocess_docx(key, bookstate)
        doc.save(key.efs_paper_path)


def wordprocess_docx(key: KeyPath, bookstate: BookState) -> docx.document.Document:
    doc = _read_document(key)
    _remove_parts_and_highlights_due_to_conditional_rendering(key, doc)
    _add_chapter_number_to_captions(key, doc, bookstate)
    _prepare_refs(key, doc, bookstate)
    _remove_images(key, doc)
    return doc


def _get_config_key(event) -> KeyPath:
    try:
        slug = event["Records"][0]["body"]
        pth = KeyPath(slug).efs_input_dir / "_config.yml"
        if not pth.exists():
            pth = KeyPath(slug).efs_input_dir / "_config.yaml"
        if not pth.exists():
            pth = KeyPath(slug).efs_input_dir / "myst.yaml"
        if not pth.exists():
            pth = KeyPath(slug).efs_input_dir / "myst.yml"
        if not pth.exists():
            raise FileNotFoundError(f"Config file not found. File: {pth}")
        return KeyPath(pth)
    except FileNotFoundError as e:
        logging.exception(f"Configuration file was not found. Error: {repr(e)}")
        raise
    except Exception as e:
        logging.exception(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _load_book_state(key: KeyPath) -> BookState:
    try:
        return BookState(key)
    except Exception as e:
        logging.exception(f"Loading book state failed. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while loading book state."
        )
        raise


# def prepare_references(
#     doc: docx.document.Document, book_metadata: dict[str, DocumentMetadata]
# ):
#     return
#     for child in doc.paragraphs[0].runs[13].element.getchildren():
#         if isinstance(child, docx.oxml.text.run.CT_Text):
#             print("child.text", child.text)
#             child.text = "666"
#             print("child.text", child.text)
#     return

#     ##### refs

#     doc.paragraphs[0].hyperlinks[0].fragment == "_Heading"
#     doc.paragraphs[0].hyperlinks[0].text == "Link to direct heading"
#     doc.paragraphs[0].hyperlinks[0].address == ""
#     doc.paragraphs[0].hyperlinks[0].url == ""

#     # check if you can replace _r with element, should be the same obj
#     doc.paragraphs[0].runs[3]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[3]._r.values() == ["002D78BD"]
#     doc.paragraphs[0].runs[3]._r.getchildren()[0].values() == ["begin"]
#     doc.paragraphs[0].runs[3]._r.getchildren()[0].tag.endswith("fldChar")
#     doc.paragraphs[0].runs[3]._r.getchildren()[0].text == ""

#     doc.paragraphs[0].runs[4]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[4]._r.values() == ["002D78BD"]
#     doc.paragraphs[0].runs[4]._r.getchildren()[0].text == r" REF _Ref193896300 \h "
#     doc.paragraphs[0].runs[4]._r.getchildren()[0].values() == ["preserve"]
#     doc.paragraphs[0].runs[4]._r.getchildren()[0].tag.endswith("instrText")
#     doc.paragraphs[0].runs[4]._r.getchildren()[0].text == ""

#     doc.paragraphs[0].runs[5]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[5]._r.values() == ["002D78BD"]
#     doc.paragraphs[0].runs[5]._r.getchildren()[0].values() == ["separate"]
#     doc.paragraphs[0].runs[5]._r.getchildren()[0].tag.endswith("fldChar")
#     doc.paragraphs[0].runs[5]._r.getchildren()[0].text == ""

#     doc.paragraphs[0].runs[6]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[6]._r.values() == ["002D78BD"]
#     doc.paragraphs[0].runs[6]._r.getchildren()[0].text == "Heading"

#     doc.paragraphs[0].runs[7]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[7]._r.values() == ["002D78BD"]
#     doc.paragraphs[0].runs[7]._r.getchildren()[0].values() == ["end"]
#     doc.paragraphs[0].runs[7]._r.getchildren()[0].tag.endswith("fldChar")
#     doc.paragraphs[0].runs[7]._r.getchildren()[0].text == ""

#     doc.paragraphs[0].runs[9]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[9]._r.values() == ["00602226"]
#     doc.paragraphs[0].runs[9]._r.getchildren()[0].values() == ["begin"]
#     doc.paragraphs[0].runs[9]._r.getchildren()[0].tag.endswith("fldChar")
#     doc.paragraphs[0].runs[9]._r.getchildren()[0].text == ""

#     doc.paragraphs[0].runs[10]._r.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[10]._r.values() == ["00602226"]
#     doc.paragraphs[0].runs[10]._r.getchildren()[0].values() == ["preserve"]
#     doc.paragraphs[0].runs[10]._r.getchildren()[0].tag.endswith("fldChar")
#     doc.paragraphs[0].runs[10]._r.getchildren()[0].text == r" REF _Ref193903648 \h "

#     doc.paragraphs[0].runs[10].element.keys()[0].endswith("rsidR")
#     doc.paragraphs[0].runs[10].element.values() == ["00602226"]
#     for child in doc.paragraphs[0].runs[13].element.getchildren():
#         if isinstance(child, docx.oxml.text.run.CT_Text):
#             child.text == "1"  # <== replace txt in ref !!
#         # ref.target_id = "f-ref-n-target-ref193903648"
#         # target.pk = "f-ref-n-target-ref193903648"
#         # target.html = '<data value=" SEQ Table \* ARABIC \">1</data>'
#         # target.text = "1"
#         # substitution.pk = "frefntargetref193903648"
#         # substitution.was = "f-ref-n-target-ref193903648"

#     ### targets


def _read_document(key: KeyPath) -> docx.document.Document:
    try:
        return docx.Document(key)
    except Exception as e:
        logger.exception(f"Unable to read document {key}. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            f"Error upon reading {key.name} document.",
        )
        raise


def _remove_parts_and_highlights_due_to_conditional_rendering(
    key: KeyPath,
    doc: docx.document.Document,
) -> None:
    try:
        return remove_parts_and_highlights_due_to_conditional_rendering(doc)
    except Exception as e:
        logger.exception(
            f"Removing parts and highlights for conditional rendering failed. "
            f"Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            f"Error in removing content meant for digital version.",
        )
        raise


def _add_chapter_number_to_captions(
    key: KeyPath,
    doc: docx.document.Document,
    bookstate: BookState,
    # docstate: DocumentState,
) -> None:
    try:
        return add_chapter_number_to_captions(key, doc, bookstate)
    except Exception as e:
        logger.exception(
            f"Adding chapter number to captions failed. " f"Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            f"Error in adding chapter numbers.",
        )
        raise


def _prepare_refs(
    key: KeyPath,
    doc: docx.document.Document,
    bookstate: BookState,
) -> None:
    try:
        return prepare_refs(key, doc, bookstate)
    except Exception as e:
        logger.exception(f"Preparing references failed. " f"Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            f"Error upon updating references with automatic numbering.",
        )
        raise


def _remove_images(
    key: KeyPath,
    doc: docx.document.Document,
) -> None:
    try:
        return remove_images(doc)
    except Exception as e:
        logger.exception(f"Removing images from .docx failed. " f"Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            f"Error in removing images for paper version.",
        )
        raise


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.PREPARER.value,
        filename=key.name,
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.FAILED.value:
        alert = AlertLog(slug=key.slug, status=AlertStatus.FAIL.value)
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")


# doc = None
# if __name__ == "__main__":
#     doc, book_metadata = lambda_handler()
#     doc.save("/tmp/efs/a_book/test.docx")
