import argparse
import datetime
import logging
import pathlib
import docx.document
import docx.shared
import docx.styles.style
import docx.text.paragraph
import docx.text.run
import docx.oxml.text.font
import docx.oxml.text.paragraph
import docx.oxml.xmlchemy
import json

try:
    from constants import IS_DEBUG
    from conditional_rendering import (
        remove_parts_and_highlights_due_to_conditional_rendering,
    )
    from metadata import DocumentMetadata
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .constants import IS_DEBUG  # type: ignore
    from .conditional_rendering import remove_parts_and_highlights_due_to_conditional_rendering  # type: ignore
    from .metadata import DocumentMetadata  # type: ignore
    from .keys import KeyPath  # type: ignore


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


def lambda_handler() -> tuple[docx.document.Document, dict[str, DocumentMetadata]]:
    key: KeyPath = KeyPath("/tmp/efs/docx2docx/")
    # book_metadata: dict[str, DocumentMetadata] = {}
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
    # for meta_file in (key / "_metadata").glob("**/*.json"):
    #     meta_file: KeyPath
    #     with meta_file.open("r") as f:
    #         metadata = DocumentMetadata(meta_file)
    #         metadata.from_json(json.load(f))
    #         book_metadata[meta_file.stem] = metadata

    book_metadata = _read_book_metadata(key)
    doc = docx.Document("/tmp/efs/docx2docx/02_assets_and_links.docx")
    remove_parts_and_highlights_due_to_conditional_rendering(doc)
    # prepare_ref_targets_in_headers(doc, book_metadata)
    # prepare_ref_targets_in_captions(doc, book_metadata)
    # prepare_ref_targets_in_footnotes(doc, book_metadata)
    # prepare_references(doc, book_metadata)
    return doc, book_metadata


def _read_book_metadata(key: KeyPath) -> dict[str, DocumentMetadata]:
    """
    Read JSON metadata stored in Elastic File System (EFS) and return a dict
    with all DocumentMetadata objects for a specific book.

    Similar to the src/builder/main/_read_book_metadata function
    """
    book_metadata: dict[str, DocumentMetadata] = {}
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


doc = None
if __name__ == "__main__":
    doc, book_metadata = lambda_handler()
    doc.save("/tmp/efs/docx2docx/test.docx")
