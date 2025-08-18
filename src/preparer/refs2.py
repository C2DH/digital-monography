import pathlib
import bs4
import docutils.nodes
import re
import secrets
import string
import functools
import typing as t

from src._common.metadata import (
    DocumentMetadata,
    HeadingDatapoint,
    RefDatapoint,
    SubstitutionDatapoint,
    TargetDatapoint,
)
from src._common.keys import KeyPath
from src._common.constants import (
    AUTONUMBER_PLACEHOLDER,
    CAPTION_ITEM_TYPE_FIGURE,
    CAPTION_ITEM_TYPE_TABLE,
    CAPTION_ITEM_TYPE_GRAPH,
    CAPTION_ITEM_TYPE_OTHER,
    CLS_CAPTION,
)
from src._common.models import Ref, Target
from src._common.state import DocumentState

# try:
#     from metadata import (
#         DocumentMetadata,
#         HeadingDatapoint,
#         RefDatapoint,
#         SubstitutionDatapoint,
#         TargetDatapoint,
#     )
#     from keys import KeyPath
#     from constants import (
#         AUTONUMBER_PLACEHOLDER,
#         CAPTION_ITEM_TYPE_FIGURE,
#         CAPTION_ITEM_TYPE_TABLE,
#         CAPTION_ITEM_TYPE_GRAPH,
#         CAPTION_ITEM_TYPE_OTHER,
#         CLS_CAPTION,
#     )
#     from models import Ref, Target
#     from state import DocumentState
# except (ImportError, ModuleNotFoundError):
#     from .metadata import (
#         DocumentMetadata,
#         HeadingDatapoint,
#         RefDatapoint,
#         SubstitutionDatapoint,
#         TargetDatapoint,
#     )
#     from .keys import KeyPath
#     from .constants import (
#         AUTONUMBER_PLACEHOLDER,
#         CAPTION_ITEM_TYPE_FIGURE,
#         CAPTION_ITEM_TYPE_TABLE,
#         CAPTION_ITEM_TYPE_GRAPH,
#         CAPTION_ITEM_TYPE_OTHER,
#         CLS_CAPTION,
#     )
#     from .models import Ref, Target
#     from .state import DocumentState


def is_header(tag: bs4.element.Tag) -> bool:
    return bool(re.match(r"^h[1-6]$", tag.name))


def is_caption(tag: bs4.element.Tag) -> bool:
    # "p", {"class": "dgt-mon-caption"}
    # return bool(tag.name == "p" and "dgt-mon-caption" in tag.attrs.get("class", []))
    return bool(tag.name == "p" and CLS_CAPTION in tag.attrs.get("class", []))


def is_footnote(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "li" and tag.attrs.get("id", "").startswith("footnote-"))


def is_reference(tag: bs4.element.Tag) -> bool:
    # "a", href=True
    return bool(tag.name == "a" and tag.attrs.get("href"))


def prepare_references(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    dstate: DocumentState,
    references: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for a_tag in references:
        a_tag: bs4.element.Tag
        if _is_target_footnote(a_tag):
            continue
        elif _is_ref_footnote(a_tag):
            footnote = Footnote(metadata.filepath)
            footnote.from_ref(a_tag["id"])
            a_tag["href"] = footnote.href
            a_tag["id"] = footnote.id
            a_tag.string = footnote.string
        else:
            pass  # process ref
            ref = Reference(a_tag)
            ref.find_infile_target(metadata.get_target(ref.id))

            link = Link(a_tag, dstate)
            target = link.find_infile_target()
            dstate.add(
                Ref(
                    fn=link.get_link_location_name(),  # TODO: change to location
                    target_id=target.pk if target else "",
                    text=link.new_link_text(),
                    href=link.new_link_href(),
                    prev_string=link.get_prev_string(),
                    prev_href=link.get_prev_href(),
                    elem=link.get_html_element(),
                    # asset_id: # NOTE: asset_id is always empty. Why?
                )
            )
            # target = metadata.get_target(link.id) if link.is_inner_reference() else None
            # metadata.add_ref(ref.to_datapoint())
            # if ref.unique_id and metadata.get_substitution(ref.unique_id) is None:
            #     metadata.add_substitution(ref.to_substitution())
    return html_soup


def _is_ref_footnote(a_tag: bs4.element.Tag) -> bool:
    if "footnote" not in a_tag["href"]:
        return False
    return bool(a_tag.attrs.get("id", "").startswith("footnote-ref-"))


def _is_target_footnote(a_tag: bs4.element.Tag) -> bool:
    return bool(a_tag.attrs.get("href", "").startswith("#footnote-ref-"))


class Link:
    def __init__(self, a_tag: bs4.Tag, dstate: DocumentState) -> None:
        """
        This should be transformed by `html2md` to
        ```md
        [link-text](link-destination)
        ```
        """

        self.a_tag = a_tag
        self.dstate = dstate

    def find_infile_target(self) -> Target | None:
        """
        Look for the link's target in a current document.
        If link leads to a target in separate document,
        or if it is an external link (e.g. to website), return None.
        """
        return None

    def get_link_location(self) -> KeyPath:
        return self.dstate.metadata.key

    def get_link_location_name(self) -> str:
        return self.get_link_location().name

    def new_link_text(self) -> str:
        """
        Markdown link text to be placed in `[text](...)` syntax.
        """
        # TODO:
        # * unique_id
        # * text_to_replace
        # * target
        # * is_cross_file_reference
        # * is_inner_reference

        tag_text = self.a_tag.text
        if AUTONUMBER_PLACEHOLDER in tag_text:
            self.text_to_replace = AUTONUMBER_PLACEHOLDER
            replace_with = r"{{ " + self.unique_id + r" }}"
            tag_text = tag_text.replace(self.text_to_replace, replace_with)
            return tag_text
        match = self._match_complex_numbering(tag_text)
        if isinstance(match, re.Match):
            start, end = match.span(1)
            self.text_to_replace = tag_text[start:end]
            replace_with = r"{{ " + self.unique_id + r" }}"
            return tag_text.replace(self.text_to_replace, replace_with)
        elif self.is_cross_file_reference():
            to_replace = ""
            for i in range(len(tag_text)):
                if tag_text[i].isdigit():
                    to_replace += tag_text[i]
                if to_replace and not tag_text[i].isdigit():
                    break
            # replace_with = r"{{ " + self.path + "#" + self.fragment + r" }}"
            replace_with = r"{{ " + self.unique_id + r" }}"
            if to_replace:
                tag_text = tag_text.replace(to_replace, replace_with)
            self.text_to_replace = to_replace
        elif self.is_inner_reference():
            if target is not None:
                to_replace = target.text
                # replace_with = r"{{ " + self.fragment + r" }}"
                replace_with = r"{{ " + self.unique_id + r" }}"
                tag_text = tag_text.replace(to_replace, replace_with)
                self.text_to_replace = to_replace
        return tag_text

    def _match_complex_numbering(self, tag_text: str) -> re.Match | None:
        """
        Search for complex numbering in the text of the anchor tag.
        Complex number pattern is one of:
            * `<digit><sep><digit>` (e.g. '1.1')
            * `<roman_num><sep><digit>` (e.g. 'iv.1')
            * `<letter of the alphabet><sep><digit>` (e.g. 'a.1')
        This solution assumes the alphabetical numbering will not be greater than 'z' (26).
        Accepted separators match MS Word separators: '.:—-'
        """
        before = r"(?:\s)"  # make sure starts with a whitespace
        heading_number = r"([ivxlcdm]+|[a-z]{1}|\d+)"
        sep = r"[.:—-]{1}"
        pattern = rf"{before}({heading_number}{sep}\d)"
        assert pattern == r"(?:\s)(([ivxlcdm]+|[a-z]{1}|\d+)[.:—-]{1}\d)"
        return re.search(pattern, tag_text.lower())

    def new_link_href(self) -> str:
        """
        Markdown destination to be placed in `[...](destination)` syntax.
        """
        # TODO:
        # * is_cross_file_reference
        # * is_inner_reference
        # * uri
        # * path
        # * fragment

        if self.is_cross_file_reference():
            # TODO: when filename tracking is in place, add handling changing paths
            path = (
                self.path.replace(".docx", ".md")
                if self.path.endswith(".docx")
                else self.path
            )
            return f"./{path}#{self.fragment}"
        elif self.is_inner_reference():
            return f"#{self.fragment}"
        return self.uri

    # target = link.find_infile_target()
    # fn=link.get_current_filename(),
    # target_id=target.pk if target else "",
    # text=link.new_link_text(),
    # href=link.new_link_href(),
    # prev_string=link.get_prev_string(),
    # prev_href=link.get_prev_href(),
    # elem=link.get_html_element(),


class Reference:
    unique_id: str
    substitution_id: str
    target_id: str
    target_fn: str
    target_fragment: str  # TODO: compare is it different than target_id?
    target_dp: TargetDatapoint | None
    a_tag: bs4.Tag
    fn: KeyPath | None
    text: str
    href: str
    prev_string: str
    prev_href: str

    def __init__(self, a_tag: bs4.Tag, fn: KeyPath | None = None) -> None:
        self.a_tag = a_tag
        self.fn = fn
        # ...

    def find_infile_target(self, metadata: DocumentMetadata):
        if self.is_internal_infile():
            self.target_dp = metadata.get_target(self.unique_id)
        # target = metadata.get_target(link.id) if self.is_inner_reference() else None

    def to_datapoint(self) -> RefDatapoint:
        pass

    def to_substitution(self) -> SubstitutionDatapoint:
        pass

    def is_external(self) -> bool:
        """
        Is it a link to an external target
        (currently only email and http protocol is recognized).
        """
        if self.href.startswith("mailto:") and "@" in self.href:
            return True
        return self.href.startswith("http") and ".sharepoint.com/" not in self.href

    def is_internal_infile(self) -> bool:
        "Is it a link to a target in the same document (file)?"
        return self.href.startswith("#")

    def is_internal_f2f(self) -> bool:
        "Is it a link to another document (file)?"
        if self.is_internal_infile() or self.is_external():
            return False
        return "#" in self.href


# def prepare_references__old(
#     html_soup: bs4.BeautifulSoup,
#     metadata: DocumentMetadata,
#     references: list[bs4.element.Tag],
# ) -> bs4.BeautifulSoup:
#     for a_tag in references:
#         a_tag: bs4.element.Tag
#         if _is_ref_footnote(a_tag):
#             footnote = FootnoteMystifier()
#             footnote.set_filepath(metadata.filepath)
#             footnote.from_ref(a_tag["id"])
#             a_tag["href"] = footnote.href
#             a_tag["id"] = footnote.id
#             a_tag.string = footnote.string
#         elif _is_target_footnote(a_tag):
#             pass
#         else:
#             link = LinkMystifier()
#             link.set_filepath(metadata.filepath)
#             link.set_from_href(a_tag["href"])
#             target = metadata.get_target(link.id) if link.is_inner_reference() else None
#             link_text = link.make_text(a_tag.text, target)
#             link_dest = link.make_destination()
#             prev_string = a_tag.string
#             prev_href = a_tag["href"]
#             a_tag.string = link_text
#             a_tag["href"] = link_dest
#             metadata.add_ref(
#                 RefDatapoint(
#                     target_id=target.pk if target else "",
#                     fn=metadata.filepath.name,
#                     text=link_text,
#                     href=link_dest,
#                     prev_string=prev_string,
#                     prev_href=prev_href,
#                     elem=str(a_tag.parent),
#                 )
#             )
#             if link.unique_id and metadata.get_substitution(link.unique_id) is None:
#                 metadata.add_substitution(
#                     SubstitutionDatapoint(
#                         pk=link.unique_id,
#                         was=link.text_to_replace,
#                         placeholder=link.unique_id,
#                         item_type="",  # item_type,
#                     )
#                 )
#     return html_soup


class Footnote:
    """
    After translation, the html should follow MyST/pandoc syntax:
        ```html
        <p> Ref of a footnote
            <sup>
                <a href="#footnote-$ID" id="footnote-ref-$ID">[footnote-$ID]</a>
            </sup>
        .</p>
        <ol>
            <li id="footnote-$ID">
              <p> Target of a footnote. <a href="#footnote-ref-$ID">↑</a></p>
            </li>
        </ol>
        ```
    where $ID is the unique_id of an instance of a footnote.

    This should be transformed by `html2md` to
        ```md
        Ref of a footnote[^footnote-$ID].
        [^footnote-$ID]: Target of a footnote.
        ```

    For more info see [docs](https://myst-parser.readthedocs.io/en/latest/syntax/typography.html#syntax-footnotes)
    """

    def __init__(self, fp: KeyPath | None):
        self.filepath: KeyPath | None = fp
        self.href: str = ""
        self.id: str = ""
        self.string: str = ""

    def _get_unique_id(self, old_id: str) -> str:
        return docutils.nodes.make_id(f"fn-{self.filepath.stem}-{old_id}")

    def from_ref(self, a_id: str) -> None:
        if not a_id.startswith("footnote-ref-"):
            return
        unique_id = self._get_unique_id(a_id[len("footnote-ref-") :])
        self.href = f"#footnote-{unique_id}"
        self.string = f"[{unique_id}]"
        # only for going back from target to ref in html, irrelevant in md
        self.id = f"footnote-ref-{unique_id}"

    def from_target(self, li_id: str) -> None:
        if li_id.startswith("footnote-") and not li_id.startswith("footnote-ref-"):
            unique_id = self._get_unique_id(li_id[len("footnote-") :])
            self.id = f"footnote-{unique_id}"
            # only for going back from target to ref in html, irrelevant in md
            self.href = f"#footnote-ref-{unique_id}"

    def __str__(self) -> str:
        return f"FootnoteMystifier(href={self.href}, id={self.id})"
