import docx
import json


from metadata import DocumentMetadata
from keys import KeyPath
from numbering_refs import prepare_refs


def _read_book_metadata(key: KeyPath) -> dict[str, DocumentMetadata]:
    """
    Read JSON metadata stored in Elastic File System (EFS) and return a dict
    with all DocumentMetadata objects for a specific book.

    Similar to the src/builder/main/_read_book_metadata function
    """
    book_metadata: dict[str, DocumentMetadata] = {}
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):  # real world
    for meta_file in (key.parent / "_metadata").glob("**/*.json"):  # toy example
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            try:
                metadata.from_json(json.load(f))
                book_metadata[meta_file.stem] = metadata
            except KeyError as e:
                print(
                    f"Invalid or obsolete metadata's Datapoint structure. Skipping "
                    f"metadata file {meta_file}. KeyError: {repr(e)}"
                )
    return book_metadata


doc = None
if __name__ == "__main__":
    # doc = docx.Document("/tmp/efs/a_book/01_a.docx")
    key = KeyPath("/tmp/efs/a_book/01_a.docx")
    doc = docx.Document(key)
    book_metadata = _read_book_metadata(key)
    prepare_refs(doc, book_metadata)
    doc.save("/tmp/efs/a_book/_paper/test_01_a.docx")
