import bs4
import pathlib
import re
import typing as t
import uuid

try:
    from metadata import AssetDatapoint, DocumentMetadata
    from constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DELETE_PREVIOUS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        METADATA_FIELDS,
    )
except (ImportError, ModuleNotFoundError):
    from .metadata import AssetDatapoint, DocumentMetadata
    from .constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DELETE_PREVIOUS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        METADATA_FIELDS,
    )

type AcceptedValues = t.Union[str, bool, pathlib.Path]
FALSE_EQUIVALENTS = [
    "0",
    "no",
    "nee",
    "not",
    "non",
    "nul",
    "none",
    "nicht",
    "nein",
    "false",
    "kein",
]


def prepare_metadata_tables(
    html_soup: bs4.BeautifulSoup,
    document_metadata: DocumentMetadata,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    """
    Find metadata tables, hide and add UUID to metadata tables.
    Hidden tables will be replaced with uuid-comment during
    transformation to markdown.
    """
    for table in tables:
        if "##" in table.text:
            metadata_tbl = MetadataTable()
            key, val = "", ""
            for tr in table.find_all(["tr"]):
                for descendent in tr.find_all():
                    if re.match(r"^\s*##\s*\w+", descendent.text):
                        key = descendent.text
                    else:
                        val = descendent.text
                if key:
                    metadata_tbl.add(key, val)
            if metadata_tbl:
                described_el = _find_described_element(table)
                caption_el = _find_related_caption(described_el)
                if (
                    metadata_tbl.includes(FIELD_DELETE_PREVIOUS)
                    and metadata_tbl.includes(FIELD_DIGITAL_SOURCE)
                    and described_el is not None
                ):
                    described_el.extract()
                table["hidden"] = "hidden"
                table["class"] = CLS_METADATA_TABLE
                table["id"] = metadata_tbl.uuid
                table[ATTRIB_METADATA_UUID] = metadata_tbl.uuid
                kwargs = metadata_tbl.to_dict()
                if described_el:
                    described_el[ATTRIB_METADATA_UUID] = metadata_tbl.uuid
                    kwargs.update({"elem": described_el})
                if caption_el:
                    caption_el[ATTRIB_METADATA_UUID] = metadata_tbl.uuid
                    kwargs.update({"caption": caption_el.text})
            asset = AssetDatapoint(pk=metadata_tbl.uuid, kwargs=kwargs)
            document_metadata.add_asset(asset)
    return html_soup


def _find_described_element(
    metadata_table: bs4.element.PageElement,
) -> t.Optional[bs4.element.Tag]:
    prev = metadata_table.previous_sibling
    while type(prev) != bs4.element.Tag:
        if not hasattr(prev, "previous_sibling"):
            return None
        prev = prev.previous_sibling
    return prev


def _find_related_caption(
    prev: t.Optional[bs4.element.Tag],
) -> t.Optional[bs4.element.Tag]:
    """
    Look backwards for a related caption, but no more than 15 siblings or until table/heading.
    """
    for _ in range(15):
        if not hasattr(prev, "previous_sibling"):
            break
        prev = prev.previous_sibling
        if hasattr(prev, "get") and "dgt-mon-caption" in prev.get("class", []):
            return prev
        elif hasattr(prev, "name") and (
            prev.name == "table" or re.match(r"^h[1-6]$", prev.name)
        ):
            break
    return None


class MetadataTable:
    """
    Container of key-value pairs extracted from a Metadata table
    that describe a single asset (e.g. license and author data
    of a single image).
    """

    def __init__(self) -> None:
        self.uuid = str(uuid.uuid4())
        self.rows = []

    def __nonzero__(self):
        return bool(self.rows)

    def __str__(self):
        return "[" + ", ".join(f"{k}={v}" for k, v in self.rows) + "]"

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, key: str) -> AcceptedValues:
        return self.get(key)

    def get(self, lookup_key: str) -> t.Optional[str]:
        try:
            return next(row[1] for row in self.rows if row[0] == lookup_key)
        except StopIteration:
            return None

    def includes(self, lookup_key: str) -> bool:
        return True if self.get(lookup_key) else False

    def add(self, key: str, val: str) -> None:
        key = self._normalize_key(key)
        val = self._normalize_val(val, key)
        self.rows.append((key, val))

    def _normalize_key(self, key: str) -> str:
        while " " in key:
            key = key.replace(" ", "")
        key = key.lower().strip().replace("_", "").replace("-", "").replace("#", "")
        for field in METADATA_FIELDS:
            if key in field["aliases"]:
                return field["key"]
        return key

    def _normalize_val(self, val: str, key: str) -> AcceptedValues:
        field_desc = next((f for f in METADATA_FIELDS if f["key"] == key), None)
        val = val.strip()
        if field_desc and field_desc["is_bool"]:
            val = val.lower()
            if val in FALSE_EQUIVALENTS:
                return False
            return bool(val)
        # TODO: after clarity on the asset storage, change this naive logic into `if fp.exists() and not fp.is_dir()` or similar
        elif key == FIELD_DIGITAL_SOURCE or key == FIELD_PAPER_SOURCE:
            return pathlib.Path(val)
        return val

    def to_dict(self) -> dict[str, AcceptedValues]:
        return {k: v for k, v in self.rows}
