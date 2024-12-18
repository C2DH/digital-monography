import bs4

try:
    from constants import ATTRIB_METADATA_UUID, CLS_METADATA_TABLE, FIELD_DIGITAL_SOURCE
    from metadata import (
        DocumentMetadata,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DIGITAL_SOURCE,
    )
    from .metadata import (
        DocumentMetadata,
    )


def insert_digital_objects(
    html_soup: bs4.BeautifulSoup,
    document_metadata: DocumentMetadata,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            pk = table.get(ATTRIB_METADATA_UUID)
            asset = document_metadata.get_asset(pk)
            default_height = "100%"
            height = asset.kwargs.get("height", default_height)
            digitalsrc = asset.kwargs.get(FIELD_DIGITAL_SOURCE, "")
            # TODO: improve conditions and verification, current method is naive at best
            if digitalsrc.suffix == ".html":
                new_tag = html_soup.new_tag("iframe")
                new_tag["src"] = str(digitalsrc)
                new_tag["width"] = "100%"
                new_tag["height"] = height
                new_tag["frameborder"] = "0"
                table.replace_with(new_tag)
            elif str(digitalsrc).startswith("https:/"):
                new_tag = html_soup.new_tag("iframe")
                new_tag["src"] = str(digitalsrc)
                new_tag["width"] = "100%"
                new_tag["height"] = height
                new_tag["frameborder"] = "0"
                table.replace_with(new_tag)
    return html_soup


def remove_metadata_tables(
    html_soup: bs4.BeautifulSoup,
    _: DocumentMetadata,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            table.extract()
    return html_soup
