import bs4

try:
    from metadata import DocumentMetadata
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata
    from .state import DocumentState


def remove_empty_tables(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    tables: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    # for table in html_soup.find_all("table"):
    for table in tables:
        res = _is_table_empty(table)
        if res:
            p = html_soup.new_tag("p")
            table.replace_with(p)
    return html_soup


def _is_table_empty(node: bs4.element.Tag) -> bool:
    if hasattr(node, "children"):
        for child in node.children:
            txt_no_whitespaces = child.text.translate(str.maketrans("", "", " \n\t\r"))
            if txt_no_whitespaces:
                return False
            else:
                _is_table_empty(child)
    return True
