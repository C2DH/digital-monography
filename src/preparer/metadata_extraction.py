import bs4
import copy
import pathlib
import re
import typing as t
import uuid

try:
    from metadata import AssetDatapoint, DocumentMetadata, MetadataTableDatapoint
    from constants import (
        MediumEnum,
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DELETE_PREVIOUS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        METADATA_FIELDS,
    )
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .metadata import AssetDatapoint, DocumentMetadata, MetadataTableDatapoint
    from .constants import (
        MediumEnum,
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DELETE_PREVIOUS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        METADATA_FIELDS,
    )
    from .keys import KeyPath

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
                target_el = _find_related_ref_target(described_el)
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
                # metadata_tbl_values = metadata_tbl.to_dict()
                document_metadata.add(
                    "metadata_tables",
                    MetadataTableDatapoint(
                        pk=metadata_tbl.uuid, kwargs=copy.copy(metadata_tbl.kwargs)
                    ),
                )
                if described_el:
                    described_el[ATTRIB_METADATA_UUID] = metadata_tbl.uuid
                    # metadata_tbl_values.update({"elem": described_el})
                    metadata_tbl.add_described_el(described_el)
                if caption_el:
                    caption_el[ATTRIB_METADATA_UUID] = metadata_tbl.uuid
                    # metadata_tbl_values.update({"caption": caption_el.text})
                    metadata_tbl.add_caption(caption_el.text)
                if target_el:
                    metadata_tbl.add_target(target_el.text)

            metadata_tbl.add_slug(document_metadata.slug)
            metadata_tbl.add_location(document_metadata.filepath)
            asset_paper = metadata_tbl.assetdatapoint_for_paper()
            asset_digital = metadata_tbl.assetdatapoint_for_digital()
            if asset_paper:
                document_metadata.add_asset(asset_paper)
            if asset_digital and asset_paper and asset_digital.fp != asset_paper.fp:
                document_metadata.add_asset(asset_digital)
            placeholder = html_soup.new_tag("span")
            placeholder.string = "% :::{dgt-mon-asset} " + metadata_tbl.uuid + " :::"
            placeholder["hidden"] = "hidden"
            table.insert_before(placeholder)

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


def _find_related_ref_target(
    prev: t.Optional[bs4.element.Tag],
) -> t.Optional[bs4.element.Tag]:
    """
    Look backwards for a related target.pk, but no more than 5 siblings or until table/heading.
    """
    for _ in range(15):
        if not hasattr(prev, "previous_sibling"):
            break
        prev = prev.previous_sibling
        if hasattr(prev, "name") and prev.name == "pre":
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
        self.kwargs = {}

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
        self.kwargs[key] = val

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

    # def to_dict(self) -> dict[str, AcceptedValues]:
    #     return {k: v for k, v in self.rows}

    def add_slug(self, slug: str) -> None:
        self.rows.append(("slug", slug))
        self.kwargs["slug"] = slug

    def add_location(self, location: t.Optional[KeyPath]) -> None:
        # print("location", location, type(location))
        if isinstance(location, pathlib.PurePath):
            location = KeyPath(location)
        self.rows.append(("location", location))
        self.kwargs["location"] = location

    def add_described_el(self, described_el: bs4.element.Tag) -> None:
        self.rows.append(("elem", described_el))
        self.kwargs["elem"] = described_el

    def add_caption(self, caption: str) -> None:
        self.rows.append(("caption", caption))
        self.kwargs["caption"] = caption

    def add_target(self, target: str) -> None:
        if target.startswith("(") and target.endswith(")="):
            target_pk = target[1:-2]
        else:
            target_pk = target
        self.rows.append(("target", target_pk))
        self.kwargs["target"] = target_pk

    def assetdatapoint_for_paper(self) -> t.Optional[AssetDatapoint]:
        if self.kwargs.get(FIELD_PAPER_SOURCE) is None:
            return None
        return AssetDatapoint(
            fp=self.kwargs[FIELD_PAPER_SOURCE],
            slug=self.kwargs["slug"],
            medium=self._get_medium(MediumEnum.PAPER),
            author=self.kwargs.get("author", ""),
            source=self.kwargs.get("source", ""),
            location=self.kwargs.get("location"),
            alttext=self._get_alttext(),
            caption=self.kwargs.get("caption", ""),
            comments=self.kwargs.get("comments", ""),
            metadata_table=self.uuid,
            target=self.kwargs.get("target", ""),
            is_color=self.kwargs.get("iscolor"),
            is_ready=self.kwargs.get("isready", False),
        )

    def assetdatapoint_for_digital(self) -> t.Optional[AssetDatapoint]:
        if self.kwargs.get(FIELD_DIGITAL_SOURCE) is None:
            return None
        return AssetDatapoint(
            fp=self.kwargs.get(FIELD_DIGITAL_SOURCE),
            slug=self.kwargs["slug"],
            medium=self._get_medium(MediumEnum.DIGITAL),
            author=self.kwargs.get("author", ""),
            source=self.kwargs.get("source", ""),
            location=self.kwargs.get("location"),
            alttext=self._get_alttext(),
            caption=self.kwargs.get("caption", ""),
            comments=self.kwargs.get("comments", ""),
            metadata_table=self.uuid,
            target=self.kwargs.get("target", ""),
            is_color=self.kwargs.get("iscolor"),
            is_ready=self.kwargs.get("isready", False),
        )

    def _get_alttext(self) -> t.Optional[str]:
        if not self.kwargs.get("alttext") and self.kwargs.get("elem"):
            elem = self.kwargs.get("elem")
            if elem:
                _alttext: bs4.element.Tag | None = elem.find(alt=True)
                if _alttext is not None:
                    return _alttext.get("alt")
        return self.kwargs.get("alttext", "")

    def _get_medium(self, medium: MediumEnum) -> MediumEnum:
        return (
            MediumEnum.PAPER_AND_DIGITAL
            if self.kwargs.get(FIELD_DIGITAL_SOURCE)
            == self.kwargs.get(FIELD_PAPER_SOURCE)
            else medium
        )
