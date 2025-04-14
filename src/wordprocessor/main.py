import argparse
import datetime
import docx.document
import json
import logging
import pathlib
import typing as t

try:
    from constants import IS_DEBUG
    from conditional_rendering import (
        remove_parts_and_highlights_due_to_conditional_rendering,
    )
    from captions_numbering import add_chapter_number_to_captions
    from metadata import DocumentMetadata
    from keys import KeyPath
    from remove_images import remove_images
except (ImportError, ModuleNotFoundError):
    from .constants import IS_DEBUG  # type: ignore
    from .conditional_rendering import remove_parts_and_highlights_due_to_conditional_rendering  # type: ignore
    from .captions_numbering import add_chapter_number_to_captions  # type: ignore
    from .metadata import DocumentMetadata  # type: ignore
    from .keys import KeyPath  # type: ignore
    from .remove_images import remove_images  # type: ignore


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path", type=str)


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_preparer.log")
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
    book_metadata = _read_book_metadata(key)
    for fp in key.efs_slug_dir.glob("*.docx"):
        doc: docx.document.Document = docx.Document(fp)
        metadata = book_metadata[fp.stem]
        remove_parts_and_highlights_due_to_conditional_rendering(doc)
        add_chapter_number_to_captions(doc, metadata)
        remove_images(doc, metadata)
        doc.save(fp.efs_slug_paper_path)


def _get_key(event) -> KeyPath:
    try:
        slug = event["Records"][0]["body"]
        pth = pathlib.Path(slug) / "_config.yml"
        return KeyPath(pth)
    except Exception as e:
        logging.exception(f"Unable to retrieve object key. Error: {repr(e)}")
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


def _read_book_metadata(key: KeyPath) -> dict[str, DocumentMetadata]:
    """
    Read JSON metadata stored in Elastic File System (EFS) and return a dict
    with all DocumentMetadata objects for a specific book.

    Similar to the src/builder/main/_read_book_metadata function
    """
    book_metadata: dict[str, DocumentMetadata] = {}
    # for meta_file in (key / "_metadata").glob("**/*.json"):
    for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            try:
                metadata.from_json(json.load(f))
                book_metadata[meta_file.stem] = metadata
            except KeyError as e:
                logger.info(
                    f"Invalid or obsolete metadata's Datapoint structure. Skipping "
                    f"metadata file {meta_file}. KeyError: {repr(e)}"
                )
    return book_metadata


# doc = None
# if __name__ == "__main__":
#     doc, book_metadata = lambda_handler()
#     doc.save("/tmp/efs/a_book/test.docx")
