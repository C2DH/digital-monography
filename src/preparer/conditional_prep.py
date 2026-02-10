import bs4

from src._common.constants import CLS_PAPER_ONLY
from src._common.state import DocumentState


def is_paper_only(tag: bs4.Tag) -> bool:
    return bool(tag.name == "span" and CLS_PAPER_ONLY in tag.attrs.get("class", []))


def remove_paper_only(
    html_soup: bs4.BeautifulSoup,
    _: DocumentState,
    paper_only: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    Remove all elements with the class "constants.CLS_PAPER_ONLY" from the html.
    See docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/#extract
    """
    for tag in paper_only:
        tag.extract()
    """
    Note the refs.prepare_references() function marks hyperlinks with paper_only class
    AFTER the whole html tree is traversed to find all paper_only elements.
    """
    for a_tag in html_soup.find_all("a", {"class": CLS_PAPER_ONLY}):
        if isinstance(a_tag, bs4.Tag):
            a_tag.extract()

    return html_soup
