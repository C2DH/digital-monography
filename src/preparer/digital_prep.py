import bs4

try:
    from constants import ATTRIB_METADATA_UUID, CLS_METADATA_TABLE, FIELD_DIGITAL_SOURCE
    from metadata import (
        DocumentMetadata,
        MetadataTableDatapoint,
    )
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .constants import (
        ATTRIB_METADATA_UUID,
        CLS_METADATA_TABLE,
        FIELD_DIGITAL_SOURCE,
    )
    from .metadata import (
        DocumentMetadata,
        MetadataTableDatapoint,
    )
    from .state import DocumentState


def insert_digital_objects(
    html_soup: bs4.BeautifulSoup,
    doc_metadata: DocumentMetadata,
    dstate: DocumentState,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            pk = table.get(ATTRIB_METADATA_UUID)
            metadata_table: MetadataTableDatapoint = doc_metadata.get_metadata_table(pk)
            default_height = "100%"
            height = metadata_table.kwargs.get("height", default_height)
            digitalsrc = str(metadata_table.kwargs.get(FIELD_DIGITAL_SOURCE, ""))
            # TODO: improve conditions and verification, current method is too naive
            if digitalsrc[-5:].lower() == ".html":
                new_tag = html_soup.new_tag("iframe")
                new_tag["src"] = digitalsrc
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


def remove_metadata_tables(
    html_soup: bs4.BeautifulSoup,
    _: DocumentMetadata,
    dstate: DocumentState,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for table in tables:
        if table.get("class", "") == CLS_METADATA_TABLE:
            table.extract()
    return html_soup
