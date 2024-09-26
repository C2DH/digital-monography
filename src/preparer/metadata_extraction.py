import json
import re
import bs4
import typing as t

try:
    from md_extraction import AssetMetadata, DocumentMetadata
    from constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        CLS_METADATA_TABLE_JSONDATA,
    )
except (ImportError, ModuleNotFoundError):
    from .md_extraction import AssetMetadata, DocumentMetadata
    from .constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        CLS_METADATA_TABLE_JSONDATA,
    )


def replace_assets_with_directives(
    html_soup: bs4.BeautifulSoup, document_metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    """
    Find, hide and add UUID to metadata tables.
    """
    for table in html_soup.find_all(["table"]):
        if "##" in table.text:
            asset_metadata = AssetMetadata()
            key, val = "", ""
            for tr in table.find_all(["tr"]):
                for descendent in tr.find_all():
                    if re.match(r"^\s*##\s*\w+", descendent.text):
                        key = descendent.text
                    else:
                        val = descendent.text
                if key:
                    asset_metadata.add(key, val)
            if asset_metadata:
                document_metadata.add_asset_metadata(asset_metadata)
                described_el = _find_described_element(table)
                caption_el = _find_related_caption(described_el)
                if (
                    asset_metadata.delete_prev
                    and asset_metadata.digital_fp
                    and described_el is not None
                ):
                    described_el.extract()
                table["hidden"] = "hidden"
                table["class"] = CLS_METADATA_TABLE
                table["id"] = asset_metadata.uuid
                table[ATTRIB_METADATA_UUID] = asset_metadata.uuid
                if described_el:
                    described_el[ATTRIB_METADATA_UUID] = asset_metadata.uuid
                if caption_el:
                    caption_el[ATTRIB_METADATA_UUID] = asset_metadata.uuid

    _hide_metadata_in_scripts_html_tag(html_soup, document_metadata)
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


def _hide_metadata_in_scripts_html_tag(
    html_soup: bs4.BeautifulSoup, document_metadata: DocumentMetadata
) -> None:
    """
    Hide all document metadata in a hidden script at the end of
    a file. Hidden tables will be replaced with uuid-comment during
    transformation to markdown.
    """
    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = CLS_METADATA_TABLE_JSONDATA
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(document_metadata.assets_as_dicts(), default=str)
    html_soup.append(json_elem)
