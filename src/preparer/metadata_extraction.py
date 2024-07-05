import json
import re
import bs4
import typing as t

try:
    from md_extraction import AssetMetadata, BookMetadata
except ModuleNotFoundError:
    from src.preparer.md_extraction import AssetMetadata, BookMetadata


def replace_assets_with_directives(
    html_soup: bs4.BeautifulSoup, metadata: BookMetadata
) -> bs4.BeautifulSoup:
    """
    Find and hide metadata tables.
    In addition, add a comment with an uuid before each metadata table.
    Later on in the document processing, this comment will be replaced with the
    object that the matadata table describes (e.g. an <img> html tag in a
    digital version).
    """
    for table in html_soup.find_all(["table"]):
        if "##" in table.text:
            asset_meta = AssetMetadata()
            key, val = "", ""
            for tr in table.find_all(["tr"]):
                for descendent in tr.find_all():
                    if re.match(r"^\s*##\s*\w+", descendent.text):
                        key = descendent.text
                    else:
                        val = descendent.text
                if key:
                    asset_meta.add(key, val)
            if asset_meta:
                metadata.add_asset_metadata(asset_meta)
                prev_el = _find_described_object(table)
                if asset_meta.delete_prev and asset_meta.digital_fp:
                    prev_el.extract()
                table["hidden"] = "hidden"
                p = html_soup.new_tag("p")
                p["class"] = "dgt-mon-asset-comment"
                p.string = "\n% :::{dgt-mon-asset} " + asset_meta.uuid
                prev_el.append(p)

    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = "dgt-mon-hidden-metadata"
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(metadata.assets_as_dicts(), default=str)
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
