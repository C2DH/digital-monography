import bs4
import docutils.nodes

from src._common.constants import (
    CLS_DIGITAL_ONLY,
    CLS_PAPER_ONLY,
)
from src._common.metadata import (
    DocumentMetadata,
)
from src._common.models import Heading, Target
from src._common.keys import KeyPath
from src._common.state import DocumentState


def prepare_ref_targets_in_headers(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,  # TODO: remove metadata
    docstate: DocumentState,
    headers: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    """
    Note targets are handled only for the digital version.
    Hence, if a link leads to `path.md#some-id`, in case of splitting docx into multiple md,
    the path.md might exist only in the digital version.
    """
    heading_count = 0
    for tag in headers:
        anchors: list[bs4.Tag] = []
        target_label = ""
        for child in tag.children:
            if isinstance(child, bs4.Tag) and child.name == "a":
                is_digital, is_paper = _get_isdigital_and_ispaper(tag, "")
                target_label = _get_target_label(docstate.key, child)
                target_tag = _create_pre_elem_for_target_label(html_soup, target_label)
                tag.insert_before(target_tag)
                anchors.append(child)
                targetdata = Target(
                    loc=docstate.key,
                    pk=target_label,  # 'f-01-a-heading'
                    html=str(tag),
                    text=tag.text,  # 'Heading'
                    elem=str(tag),
                    item_type="heading",
                    is_digital=is_digital,
                    is_paper=is_paper,
                    filename=docstate.key.name if docstate.key else None,
                    fragment=child.get("id"),  # '_Heading'
                    prefix="",
                    file_count=metadata.get_chapter_number(),  # 1 # TODO: get from somewhere else
                    prev_item_num=None,
                )
                # print("add_target", targetdata.model_dump())
                docstate.add(targetdata)
        h_lvl = "".join(ch for ch in tag.name if ch.isdigit())
        heading_count += 1
        hdata: Heading = Heading(
            loc=docstate.key,
            slug=docstate.metadata.slug,
            file_name=docstate.key.name if docstate.key else "",  # 1
            h_num=heading_count,  # 2
            text=tag.text,  # 'Heading'
            target=target_label,  # 'f-01-a-a-heading'
            word_count=metadata.word_count,  # 258
            char_count=metadata.char_count,  # 1039
            level=h_lvl,  # 2
            elem=str(tag),
        )
        docstate.add(hdata)
        for a in anchors:
            a.extract()
    return html_soup


def _get_isdigital_and_ispaper(
    partent_tag: bs4.Tag, identifier: str
) -> tuple[bool, bool]:
    """
    When a user highlights some text with a color set in constants.MAMMOTH_STYLE_MAP,
    mammoth sets an appropriate css class to the outputed html.
    This function iterates over descendant elements looking for the said css classes.
    """
    css_classes = [
        tag.get("class", [])
        for tag in partent_tag.descendants
        if isinstance(tag, bs4.element.Tag) and (identifier in tag.text)
    ]
    css_classes: list[str] = [item for sublist in css_classes for item in sublist]
    is_digital = is_paper = True
    if CLS_DIGITAL_ONLY in css_classes and CLS_PAPER_ONLY in css_classes:
        is_digital = is_paper = None
    elif CLS_DIGITAL_ONLY in css_classes:
        is_paper = False
    elif CLS_PAPER_ONLY in css_classes:
        is_digital = False
    return is_digital, is_paper


def _get_target_label(curr_key: KeyPath, elem: bs4.Tag) -> str:
    """
    If we have `<a id="_Heading"></a>` in `01_a.md` file, the return value is
    `f-01-a-heading`.

    Where
        `f` is a prefix, needed so that label doesn't start with a number,
        `01-a` is slugified name of the current file where a target is placed,
        `heading` is slugified id from <a> tag.
    """
    prefix = "f"
    path = curr_key.stem
    tag_id = elem.get("id", "").replace("_", "-")
    assert tag_id, "Unknown situation where <a> tag has no id attribute"
    fragment_before_slugification = f"{prefix}-{path}-{tag_id}"
    return docutils.nodes.make_id(fragment_before_slugification)


def _create_pre_elem_for_target_label(
    html_soup: bs4.BeautifulSoup, label: str
) -> bs4.Tag:
    """
    Creates `<pre>(f-file-heading-3)=</pre>` tag.
    This is meant to be inserted just before the targeted html element.
    <pre> tags (preformatted text elements) are meant to be presented exactly as is,
    so they are not processed by html2md converter.
    """
    new_tag = html_soup.new_tag("pre")
    new_tag.string = f"({label})="
    return new_tag
