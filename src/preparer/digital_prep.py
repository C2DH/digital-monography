import bs4

try:
    from constants import CLS_METADATA_TABLE
    from metadata import (
        DocumentMetadata,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import CLS_METADATA_TABLE
    from .metadata import (
        DocumentMetadata,
    )


def insert_digital_objects(
    html_soup: bs4.BeautifulSoup,
    document_metadata: DocumentMetadata,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
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
