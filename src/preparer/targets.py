import bs4
import typing as t

try:
    from metadata import (
        DocumentMetadata,
        HeadingDatapoint,
        RefDatapoint,
        SubstitutionDatapoint,
        TargetDatapoint,
    )
    from keys import KeyPath
    from constants import (
        CAPTION_ITEM_TYPE_FIGURE,
        CAPTION_ITEM_TYPE_TABLE,
        CAPTION_ITEM_TYPE_GRAPH,
        CAPTION_ITEM_TYPE_OTHER,
        CLS_CAPTION,
    )
    from models import Ref, Target
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .metadata import (
        DocumentMetadata,
        HeadingDatapoint,
        RefDatapoint,
        SubstitutionDatapoint,
        TargetDatapoint,
    )
    from .keys import KeyPath
    from .constants import (
        CAPTION_ITEM_TYPE_FIGURE,
        CAPTION_ITEM_TYPE_TABLE,
        CAPTION_ITEM_TYPE_GRAPH,
        CAPTION_ITEM_TYPE_OTHER,
        CLS_CAPTION,
    )
    from .models import Ref, Target
    from .state import DocumentState


def prepare_ref_targets_in_headers(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    headers: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    return html_soup


def prepare_ref_targets_in_captions(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    captions: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    return html_soup


def prepare_ref_targets_in_footnotes(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    footnotes: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    return html_soup
