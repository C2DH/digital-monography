import json
import re
import bs4
import typing as t

try:
    from md_extraction import AssetMetadata, DocumentMetadata
    from constants import CLS_METADATA_TABLE, CLS_METADATA_TABLE_JSONDATA
except (ImportError, ModuleNotFoundError):
    from .md_extraction import AssetMetadata, DocumentMetadata
    from .constants import CLS_METADATA_TABLE, CLS_METADATA_TABLE_JSONDATA


def replace_assets_with_directives(
    html_soup: bs4.BeautifulSoup, document_metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    """
    Find, hide and add UUID to metadata tables.
    In addition, hide all document metadata in a hidden script at the end of
    a file. Hidden tables will be replaced with uuid-comment during
    transformation to markdown.
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
                if asset_metadata.delete_prev and asset_metadata.digital_fp:
                    prev_el = _find_described_object(table)
                    prev_el.extract()
                table["hidden"] = "hidden"
                table["class"] = CLS_METADATA_TABLE
                table["id"] = asset_metadata.uuid

    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = CLS_METADATA_TABLE_JSONDATA
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(document_metadata.assets_as_dicts(), default=str)
    html_soup.append(json_elem)
    return html_soup


def _find_described_object(
    metadata_table: bs4.element.PageElement,
) -> t.Optional[bs4.element.Tag]:
    prev = metadata_table.previous_sibling
    while type(prev) != bs4.element.Tag:
        if not hasattr(prev, "previous_sibling"):
            return None
        prev = prev.previous_sibling
    return prev
