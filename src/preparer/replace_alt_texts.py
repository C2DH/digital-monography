import bs4

from src._common.metadata import DocumentMetadata
from src._common.state import DocumentState


def is_img_with_alt_text(tag: bs4.element.Tag) -> bool:
    # "img", alt=True
    return bool(tag.name == "img" and tag.attrs.get("alt"))


def prepare_alt_texts(
    soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    images: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    # for img in soup.find_all("img", alt=True):
    for img in images:
        img["alt"] = img["alt"].replace("\n", " ")
    return soup
