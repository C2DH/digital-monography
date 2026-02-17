import bs4

from src._common.constants import ATTRIB_METADATA_UUID, CLS_METADATA_TABLE
from src._common.models import Asset, AssetService
from src._common.state import DocumentState


DEFAULT_HEIGHT = "100%"


def insert_digital_objects(
    html_soup: bs4.BeautifulSoup,
    # doc_metadata: DocumentMetadata,
    docstate: DocumentState,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            pk = table.get(ATTRIB_METADATA_UUID)
            # metadata_table: MetadataTableDatapoint = doc_metadata.get_metadata_table(pk)
            # default_height = "100%"
            asset = _find_asset(docstate, metadata_table_pk=pk)
            if asset is None:
                height = DEFAULT_HEIGHT
                digitalsrc = ""
            else:
                height = asset.height
                digitalsrc = str(asset.fp)
            # assets: list[Asset] = docstate.filter("assets", pk, attrib="metadata_table")
            # print("\nassets", len(assets), assets, "\n")
            # tablename: str, val: str | int, attrib: str = "pk"
            # height = metadata_table.kwargs.get("height", default_height)
            # digitalsrc = str(metadata_table.kwargs.get(FIELD_DIGITAL_SOURCE, ""))
            # TODO: improve conditions and verification, current method is too naive
            if digitalsrc[-5:].lower() == ".html":
                new_tag = html_soup.new_tag("iframe")
                # "./../assets/fig2.html" instead of "assets/fig2.html"
                new_tag["src"] = f"./../{digitalsrc}"
                new_tag["width"] = "100%"
                new_tag["height"] = height
                new_tag["frameborder"] = "0"
                table.replace_with(new_tag)
            elif (
                digitalsrc[:7].lower() == "https:/"
                or digitalsrc[:6].lower() == "http:/"
            ):
                new_tag = html_soup.new_tag("iframe")
                new_tag["src"] = digitalsrc
                new_tag["width"] = "100%"
                new_tag["height"] = height
                new_tag["frameborder"] = "0"
                table.replace_with(new_tag)
    return html_soup


def _find_asset(docstate: DocumentState, metadata_table_pk: str) -> Asset | None:
    assets: list[Asset] = docstate["assets"]
    for asset in assets:
        if asset.metadata_table == metadata_table_pk and AssetService.is_digital(
            asset.medium
        ):
            return asset
    return None


def remove_metadata_tables(
    html_soup: bs4.BeautifulSoup,
    _: DocumentState,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            table.extract()
    return html_soup
