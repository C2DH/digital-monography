import datetime
import json
import typing as t

try:
    from metadata import DocumentMetadata
    from keys import KeyPath
    from verif_warnings import MessagesJson, VerifierMessages
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata
    from .keys import KeyPath
    from .verif_warnings import MessagesJson, VerifierMessages


class BookVerifier:
    def __init__(self) -> None:
        self._messages = VerifierMessages()
        self._metadatas: t.Dict[str, DocumentMetadata] = {}

    def to_json(self, md: bool = False) -> MessagesJson:
        return self._messages.to_json(md)

    def sort(self) -> None:
        self._messages.sort(key=lambda msg: (msg["line"], msg["pos"]))

    def verify(self, key: KeyPath, timestamp: datetime.datetime) -> VerifierMessages:
        self._parse_metadata(key)
        return self._messages

    def _parse_metadata(self, key: KeyPath) -> None:
        for fp in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
            st_size = fp.stat().st_size
            if st_size < 126:
                continue
            with open(fp, "rb") as infile:
                md = DocumentMetadata()
                md.from_json(json.load(infile))
                self._metadatas[fp.stem] = md
                print("DocumentMetadata", md)
                # for domain, tbl in tables.items():
                #     records[domain].extend(records_in_one_file.get(domain, []))

        pass
