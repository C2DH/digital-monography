import argparse
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
    from conditional_rendering import (
        remove_parts_and_highlights_due_to_conditional_rendering,
    )
    from metadata import DocumentMetadata
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .conditional_rendering import (
        remove_parts_and_highlights_due_to_conditional_rendering,
    )
    from .metadata import DocumentMetadata
    from .keys import KeyPath


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path", type=str)


def lambda_handler() -> docx.document.Document:
    book_metadata: dict[str, DocumentMetadata] = {}
    key: KeyPath = KeyPath("/tmp/efs/docx2docx/")
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
    for meta_file in (key / "_metadata").glob("**/*.json"):
        meta_file: KeyPath
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            metadata.from_json(json.load(f))
            book_metadata[meta_file.stem] = metadata

    doc = docx.Document("/tmp/efs/docx2docx/02_assets_and_links.docx")
    remove_parts_and_highlights_due_to_conditional_rendering(doc)
    # prepare_ref_targets_in_headers(doc, book_metadata)
    # prepare_ref_targets_in_captions(doc, book_metadata)
    # prepare_ref_targets_in_footnotes(doc, book_metadata)
    # prepare_references(doc, book_metadata)
    return doc, book_metadata


doc = None
if __name__ == "__main__":
    doc, book_metadata = lambda_handler()
    doc.save("/tmp/efs/docx2docx/test.docx")
