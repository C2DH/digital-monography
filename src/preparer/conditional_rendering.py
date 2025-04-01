import bs4


try:
    from constants import CLS_PAPER_ONLY
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .constants import CLS_PAPER_ONLY
    from .metadata import DocumentMetadata


def is_paper_only(tag: bs4.Tag) -> bool:
    return bool(tag.name == "span" and CLS_PAPER_ONLY in tag.attrs.get("class", []))


def remove_paper_only(
    html_soup: bs4.BeautifulSoup, _: DocumentMetadata, paper_only: list[bs4.Tag]
) -> bs4.BeautifulSoup:
    """
    Remove all elements with the class "constants.CLS_PAPER_ONLY" from the html.
    See docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/#extract
    """
    for tag in paper_only:
        tag.extract()
    return html_soup
