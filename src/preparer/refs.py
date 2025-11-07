"""
NOTE: This module is in dire need of refactoring.
It is a mess of functions and classes that do not follow any particular pattern.
Dear future me, please refactor it at the next time you need to touch referencing logic.
"""

# This module handles references and targets compliant with the old
# Jupyter Book v1 specification.

import pathlib
import bs4
import docutils.nodes
import re
import secrets
import string
import functools
import typing as t
import uuid

from src._common.constants import (
    AUTONUMBER_PLACEHOLDER,
    CAPTION_ITEM_TYPE_FIGURE,
    CAPTION_ITEM_TYPE_TABLE,
    CAPTION_ITEM_TYPE_GRAPH,
    CAPTION_ITEM_TYPE_OTHER,
    CLS_CAPTION,
    CLS_DIGITAL_ONLY,
    CLS_PAPER_ONLY,
)
from src._common.metadata import (
    DocumentMetadata,
    HeadingDatapoint,
    RefDatapoint,
    SubstitutionDatapoint,
    TargetDatapoint,
)
from src._common.models import Heading, Ref, RefTarget, Substitution, Target
from src._common.keys import KeyPath
from src._common.state import DocumentState


def is_reference(tag: bs4.element.Tag) -> bool:
    # "a", href=True
    return bool(tag.name == "a" and tag.attrs.get("href"))
    # return bool(
    #     tag.name == "a"
    #     and tag.attrs.get("href")
    #     and tag.attrs.get("id", "").startswith("footnote")
    # )


# def print(*args, **kwargs):
#     # disable all print statements in the module
#     pass
#     # __builtins__.print(*args, **kwargs)


"""
===INFILE=========================================================
Say a_tag in file "05_conditional-rendering.docx" is
`<a href="#_Ref193102947">Figure 1</a>`

Link
id # f-05-conditional-rendering-ref193102947 # USED to be target_id
unique_id # f05conditionalrenderingref193102947 # substitution_id
text_to_replace # "1" extracted from prev_string="Figure 1" ("was" in Substitution)
make_text() # get text to put into [text](...)
make_destination() # ..to put into [...](destination)

<a href="#f-05-conditional-rendering-ref193102947">Figure {{ f05conditionalrenderingref193102947 }}</a>

text=Figure {{ f05conditionalrenderingref193102947 }}
dest=#f-05-conditional-rendering-ref193102947
     ^  fragment
===F2F============================================================
Say a_tag in file "01_a.docx" is
<a href="02_b.docx#tblSimpleTable">link in caption to a table in chapter 2</a>

Link
id # f-02-b-tblsimpletable # USED to be target_id
unique_id # 02bdocxf02btblsimpletable # substitution_id
text_to_replace # "2" extracted from prev_string="link in caption to a table in chapter 2" ("was" in Substitution)
make_text() # get text to put into [text](...)
make_destination() # ..to put into [...](destination)

<a href="./02_b.md#f-02-b-tblsimpletable">link in caption to a table in chapter {{ 02bdocxf02btblsimpletable }}</a>

text=link in caption to a table in chapter {{ 02bdocxf02btblsimpletable }}
dest=./02_b.md#f-02-b-tblsimpletable
        path  ^  fragment
=================================================================
"""


def prepare_references(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    docstate: DocumentState,
    references: list[bs4.Tag],
) -> bs4.BeautifulSoup:
    """
    There are 4 types of references:
    * footnotes, handled in footnotes.py
    * external, e.g. email or http link
    * internal in-file, e.g. #some-id
    * internal file-to-file, e.g. otherfile.md#some-id

    Input for external:
        <a href="http:/example.com">link to a website</a>
    Expected output (no change):
        <a href="http:/example.com">link to a website</a>

    Input for internal in-file:
        <a href="#_Ref193102947">Figure 1</a>
    Expected output:
        <a href="#f-01-my-file-ref193102947">Figure {{ f01myfileref193102947 }}</a>

    Input for internal file-to-file:
        <a href="01_a.docx#bookmarkToTbl">link to a table in chapter 1</a>
    Expected output:
        <a href="./01_a.md#f-01-a-bookmarktotbl">link to a table in chapter {{ 01adocxf01abookmarktotbl }}</a>
    """
    for chpt in docstate.__dict__.get("chapters"):
        print("chapter in docstate", chpt)

    for a_tag in references:
        print("=" * 75)
        print("a_tag", a_tag)
        if _is_ref_footnote(a_tag) or _is_target_footnote(a_tag):
            # handled in footnotes.py
            continue
        # print(
        #     "_check_if_link_marked_as_paper_only(a_tag)",
        #     _check_if_link_marked_as_paper_only(a_tag),
        # )
        # if _check_if_link_marked_as_paper_only(a_tag):

        #     tag_class = a_tag.get("class", [])
        #     tag_class.append(CLS_PAPER_ONLY)
        #     a_tag["class"] = tag_class

        _mark_paper_only_tag(a_tag)
        print("POST_a_tag", a_tag)

        fn, fragment = _get_fn_and_fragment_from_href(a_tag["href"])
        # fragment = docutils.nodes.make_id(fragment)  # slugify consistently with targets
        # is_internal = _is_internal(a_tag["href"], fn, fragment)
        print("/n/n===")
        print(f"fn={fn}, fragment={fragment}")
        ref_targets = _find_ref_targets(docstate, a_tag["href"], fn, fragment)
        print("ref_targets", ref_targets)

        print(
            "a_tag > after paperonly handling", a_tag
        )  # <a class="dgt-mon-paper-only" href="#figForPaper"><span class="dgt-mon-paper-only">link to figForPaper bookmark</span></a>
        link = LinkMystifier()
        # take current file and href from <a> tag
        # use urllib.urlsplit to parse href
        print("metadata.filepath", metadata.filepath)
        link.set_filepath(metadata.filepath)
        print('a_tag["href"]', a_tag["href"])
        link.set_from_href(a_tag["href"])
        print("link.id", link.id)
        # if is inner reference, get a target
        # target = metadata.get_target(link.id) if link.is_inner_reference() else None
        target = docstate.get("targets", link.id) if link.is_inner_reference() else None
        print("target", target)

        # ref_target = docstate.get("ref_targets", link.id, "proc_href")
        # print(">.> ref_target", ref_target)

        # get text to put into [text](...)
        link_text = link.make_text(a_tag.text, target)
        print("link_text", link_text)
        # get dest to put into [...](destination)
        link_dest = link.make_destination()
        print("link_dest", link_dest)
        prev_string = a_tag.string if a_tag.string is not None else ""

        print("prev_string", prev_string)
        print("a_tag.string", a_tag.string)
        print('a_tag["href"]', a_tag["href"])
        print(
            "a_tag > before string replacement", a_tag
        )  # <a class="dgt-mon-paper-only" href="#figForPaper"><span class="dgt-mon-paper-only">link to figForPaper bookmark</span></a>
        prev_href = a_tag["href"]
        a_tag.string = link_text
        a_tag["href"] = link_dest
        print(
            "a_tag > after string replacement", a_tag
        )  # <a class="dgt-mon-paper-only" href="#f-05-conditional-rendering-figforpaper">link to figForPaper bookmark</a>
        ref = RefDatapoint(
            target_id=target.pk if target else "",
            fn=metadata.filepath.name,
            text=link_text,
            href=link_dest,
            prev_string=prev_string,
            prev_href=prev_href,
            elem=str(a_tag.parent),
        )
        print("RefDatapoint", ref)
        metadata.add_ref(ref)
        data = Ref(
            loc=docstate.key,
            target_id=target.pk if target else "",
            fn=docstate.key.name if docstate.key else "",
            text=link_text,
            href=link_dest,
            prev_string=prev_string,
            prev_href=prev_href,
            elem=str(a_tag.parent),
        )
        print("Ref", data.model_dump())
        docstate.add(data)
        # Ref(
        #     loc=dstate.key,
        #     target_id=target.pk if target else "",
        #     fn=dstate.key.name if dstate.key else "",
        #     text=link_text,
        #     href=link_dest,
        #     prev_string=prev_string,
        #     prev_href=prev_href,
        #     elem=str(a_tag.parent),
        # )
        # )
        print("link.unique_id", link.unique_id)  # f05conditionalrenderingref193102988
        print(
            "metadata.get_substitution(link.unique_id)",
            metadata.get_substitution(link.unique_id),
        )
        # TODO: get substitution from docstate
        # if link.unique_id and metadata.get_substitution(link.unique_id) is None:
        if link.unique_id and docstate.get("substitutions", link.unique_id) is None:
            # get chapter number from the href if f2f else number from current file
            # TODO: more logic to take the chapter number AFTER the split
            target_chapter_number = (
                metadata.get_chapter_number(link.path)
                if link.path and link.is_cross_file_reference()
                else metadata.get_chapter_number()
            )
            print("target_chapter_number", target_chapter_number)
            print("link.path", link.path)
            if link.path and link.is_cross_file_reference():
                target_fn = KeyPath(link.path).name
                print("KeyPath(link.path).name", target_fn)
            elif metadata.filepath and link.is_inner_reference():
                target_fn = metadata.filepath.name
                # TODO: get from docstate
                print("metadata.filepath.name", target_fn)
            else:
                target_fn = None
            # target_fn = (
            #     link.path if link.path and link.is_cross_file_reference() else None
            # )
            metadata.add_substitution(
                SubstitutionDatapoint(
                    pk=link.unique_id,
                    was=link.text_to_replace,
                    # placeholder=link.unique_id,
                    placeholder=link.id,
                    item_type="ref",
                    is_digital=None,
                    is_paper=None,
                    location=metadata.filepath,
                    target_fn=target_fn,
                    file_count=target_chapter_number,
                    prefix="",
                    prev_item_num=None,
                )
            )
            data = Substitution(
                loc=docstate.key,
                pk=link.unique_id,
                hash="",
                was=link.text_to_replace,
                # placeholder=link.unique_id,
                placeholder=link.id,
                item_type="ref",
                is_digital=None,
                is_paper=None,
                location=metadata.filepath,
                target_fn=target_fn,
                file_count=target_chapter_number,
                prefix="",
                prev_item_num=None,
            )
            print("S>", data.model_dump())
            docstate.add(data)
            # docstate.add(
            #     Substitution(
            #         loc=docstate.key,
            #         pk=link.unique_id,
            #         was=link.text_to_replace,
            #         # placeholder=link.unique_id,
            #         placeholder=link.id,
            #         item_type="ref",
            #         is_digital=None,
            #         is_paper=None,
            #         location=metadata.filepath,
            #         target_fn=target_fn,
            #         file_count=target_chapter_number,
            #         prefix="",
            #         prev_item_num=None,
            #     )
            # )
        print("post a_tag", a_tag)
    return html_soup


def _is_ref_footnote(a_tag: bs4.element.Tag) -> bool:
    if "footnote" not in a_tag["href"]:
        return False
    return bool(a_tag.attrs.get("id", "").startswith("footnote-ref-"))


def _is_target_footnote(a_tag: bs4.element.Tag) -> bool:
    return bool(a_tag.attrs.get("href", "").startswith("#footnote-ref-"))


def _mark_paper_only_tag(a_tag: bs4.Tag) -> None:
    """
    The way it is implemented now, "paper-only" css class will mark only
    descendants of the hyperlink tag and not the hyperlink tag itself.
    `<a href="https://example.com"><span class="dgt-mon-paper-only">text</span></a>`
    This is because in OOXML, highlight is a property of runs inside of hyperlink tag,
    while the hyperlink tag itself is not considered highlited. This enables .docx users
    to have different highlights in the same hyperlink element, but requires additional
    processing from the preparer microservice.

    To mitigate that, iterate over descendents and check if all of them are marked
    as paper-only.
    If yes, mark the hyperlink tag as paper-only as well.
    """
    res = set()
    for tag in a_tag.descendants:
        if isinstance(tag, bs4.Tag) and tag.get("class", []) == [CLS_PAPER_ONLY]:
            res.add(True)
        elif isinstance(tag, bs4.NavigableString):
            pass
        else:
            res.add(False)
    if not res:
        return
    is_paper_only = all(res)
    if is_paper_only:
        tag_class = a_tag.get("class", [])
        tag_class.append(CLS_PAPER_ONLY)
        a_tag["class"] = tag_class


def _check_if_link_marked_as_paper_only(a_tag: bs4.Tag) -> bool:
    """
    The way it is implemented now, "paper-only" css class will mark only
    descendants of the hyperlink tag and not the hyperlink tag itself.
    `<a href="https://example.com"><span class="dgt-mon-paper-only">text</span></a>`
    This is because in OOXML, highlight is a property of runs inside of hyperlink tag,
    while the hyperlink tag itself is not considered highlited. This enables .docx users
    to have different highlights in the same hyperlink element, but requires additional
    processing from the preparer microservice.

    To mitigate that, iterate over descendents and check if all of them are marked
    as paper-only.
    """
    res = set()
    for tag in a_tag.descendants:
        if isinstance(tag, bs4.Tag) and tag.get("class", []) == [CLS_PAPER_ONLY]:
            res.add(True)
        elif isinstance(tag, bs4.NavigableString):
            pass
        else:
            res.add(False)
    if not res:
        return False
    return all(res)


class LinkMystifier:
    """
    Translate html anchor tags to MyST/markdown link syntax.
    """

    _scheme_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-."
    _unsafe_url_bytes_to_remove = ["\t", "\r", "\n"]
    _prefix = "f"

    def __init__(self):
        self.filepath: t.Optional[KeyPath] = None
        self.uri: str = ""
        self.scheme: str = ""
        self.netloc: str = ""
        self.path: str = ""
        self.query: str = ""
        self.fragment: str = ""
        self.text_to_replace: str = ""
        # cached functions
        self.is_external_url = functools.lru_cache()(self._is_external_url__uncached)
        self.is_cross_file_reference = functools.lru_cache()(
            self._is_cross_file_reference__uncached
        )
        self.is_inner_reference = functools.lru_cache()(
            self._is_inner_reference__uncached
        )

    @property
    def id(self) -> str:
        return self.fragment

    def mystify_target(self) -> str:
        """
        MyST markdown target in one of the appropriate syntaxes:
            `(heading-target)=`
        See the [docs](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html)
        for more information.
        """
        # TODO: `{#paragraph-target}`
        # TODO: `[span_with_an_id]{#span-target}`
        return f"({self.fragment})="

    def set_filepath(self, fn: t.Optional[KeyPath]) -> None:
        self.filepath = fn

    def set_from_href(self, href: str) -> None:
        self.uri = href
        self.scheme, self.netloc, self.path, self.query, fragment = self._urlsplit(href)
        self.fragment = fragment

    def set_from_id(self, id: str) -> None:
        self.fragment = id

    @property
    def fragment(self) -> str:
        return self._fragment

    @fragment.setter
    def fragment(self, val: str):
        self._fragment = self._slugify(val)

    def _slugify(self, val: str) -> str:
        if not val:
            return val
        if self.filepath and self.path:
            path = pathlib.Path(self.path)
            return docutils.nodes.make_id(f"{self._prefix}-{path.stem}-{val}")
        elif self.filepath and not self.path:
            return docutils.nodes.make_id(f"{self._prefix}-{self.filepath.stem}-{val}")
        else:
            return docutils.nodes.make_id(f"{self._prefix}-{val}")

    @property
    def unique_id(self) -> str:
        if self.is_cross_file_reference():
            unique_id = self.path + "#" + self.fragment
        elif self.is_inner_reference():
            unique_id = self.fragment
        else:
            unique_id = self.fragment
        # removal of escape chars is important for substitution
        return (
            unique_id.replace("-", "")
            .replace(".", "")
            .replace("#", "")
            .replace("_", "")
        )

    def _urlsplit(self, url: str, scheme: str = "") -> tuple[str, str, str, str, str]:
        """
        Splits url into the following parts:
            <scheme>://<net_loc>/<path>;<params>?<query>#<fragment>
        Function is based on urllib.parse.urlsplit()
        Relative references, like
            <a href="#Heading">Link</a>
        result in fragment="Heading"
            <a href="filename.docx#Heading">Link</a>
        result in path="filename.docx", fragment="Heading"
        """
        for b in self._unsafe_url_bytes_to_remove:
            url = url.replace(b, "")
            scheme = scheme.replace(b, "")

        query = fragment = ""
        i = url.find(":")
        if i > 0 and url[0].isascii() and url[0].isalpha():
            for c in url[:i]:
                if c not in self._scheme_chars:
                    break
            else:
                scheme, url = url[:i].lower(), url[i + 1 :]

        netloc, url = self._get_netloc(url)
        if "#" in url:
            url, fragment = url.split("#", 1)
        if "?" in url:
            url, query = url.split("?", 1)
        return scheme, netloc, url, query, fragment

    def _get_netloc(self, url: str) -> tuple[str, str]:
        """
        Network location, as per [RFC 1808](https://datatracker.ietf.org/doc/html/rfc1808.html)
        """
        start = 2
        netloc = ""
        if url[:start] == "//":
            delim = len(url)  # position of end of domain part of url, default is end
            for c in "/?#":  # look for delimiters; the order is NOT important
                wdelim = url.find(c, start)  # find first of this delim
                if wdelim >= 0:  # if found
                    delim = min(delim, wdelim)  # use earliest delim position
            netloc = url[start:delim]  # domain
            url = url[delim:]  # rest
        return netloc, url

    def _is_external_url__uncached(self) -> bool:
        """E.g. 'https://example.com'"""
        return all([self.scheme, self.netloc])

    def _is_cross_file_reference__uncached(self) -> bool:
        """E.g. 'filename.docx#Heading'"""
        if self.is_external_url():
            return False
        return all([self.fragment, self.path])

    def _is_inner_reference__uncached(self) -> bool:
        """E.g. '#Heading'"""
        if self.is_external_url() or self.path:
            return False
        return bool(self.fragment)

    def make_destination(self) -> str:
        """
        Markdown destination to be placed in `[...](destination)` syntax.
        """
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

    def make_text(
        self, tag_text: str, target: t.Optional[TargetDatapoint] = None
    ) -> str:
        """
        Markdown link text to be placed in `[text](...)` syntax.
        """
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

    def __str__(self) -> str:
        return f"LinkMystifier(scheme={self.scheme}, netloc={self.netloc}, path={self.path}, query={self.query}, fragment={self.fragment})"

    def _match_complex_numbering(self, tag_text: str) -> re.Match | None:
        """
        Search for complex numbering in the text of the anchor tag.
        Complex number pattern is either `<roman_num><sep><digit>` (e.g. 'iv.1')
        or `<letter of the alphabet><sep><digit>` (e.g. 'a.1') or `<digit><sep><digit>`.
        This solution assumes the alphabetical numbering will not be greater than 'z' (26).
        Accepted separators match MS Word separators: '.:—-'
        """
        before = r"(?:\s)"  # make sure starts with a whitespace
        heading_number = r"([ivxlcdm]+|[a-z]{1}|\d+)"
        sep = r"[.:—-]{1}"
        pattern = rf"{before}({heading_number}{sep}\d)"
        assert pattern == r"(?:\s)(([ivxlcdm]+|[a-z]{1}|\d+)[.:—-]{1}\d)"
        return re.search(pattern, tag_text.lower())
        # r"(?:\s)(([ivxlcdm]+|[a-z]{1}|\d+)[.:—-]{1}\d)", tag_text.lower()


def _get_fragment_from_anchor_href(a_tag: bs4.Tag) -> str:
    """
    Given an anchor tag id like `<a id="_Ref193102947"></a>` or `<a id="a_Heading"></a>`,
    return the fragment identifier, e.g. `ref193102947` or `a-heading`.
    Make sure fragment slugification is consistent with reference preparation.
    """
    tag_href = a_tag.get("href", "")
    return tag_href
    # return docutils.nodes.make_id(tag_href) # maybe slugification is not needed since we are using hash as id anyway?


def _get_fn_and_fragment_from_href(href: str) -> tuple[str, str]:
    """
    Extracts filename and fragment identifier from an URI.
    If a value is not present, an empty string is returned instead.

    E.g. "manuscript.docx" and "fragment" from:
        "https://sharepoint.com/some/path/manuscript.docx#fragment"
        "./manuscript.docx#fragment"
    """
    # 'A fragment identifier component is indicated by the presence of a number sign ("#")'
    # so it should always be an index of #.
    # See https://www.rfc-editor.org/rfc/rfc3986#section-3.5
    if "#" in href:
        fragment_idx = href.index("#")
    else:
        fragment_idx = len(href)
    path = href[:fragment_idx]
    fragment = href[fragment_idx + 1 :]
    if "." not in path:
        return "", fragment
    for scheme in ["tel:", "mailto:", "sms:", "javascript:"]:
        if path.startswith(scheme):
            return "", fragment
    if "/" not in path:
        return path, fragment
    filename = ""
    for i in range(len(path) - 1, -1, -1):
        ch = path[i]
        # if ch == ".":
        #     suffix = path[i + 1 :]
        if ch == "/":
            filename = path[i + 1 :]
            break
    if "." not in filename:
        return "", fragment
    return filename, fragment


def _is_internal(href: str, filename: str, fragment: str) -> bool:
    """
    Returns if a resource is internal (either in the same file or f2f).
    By internal, we mean there is some particular fragment in some particular file.
    Does not matter is the file is hosted remotely in some external source (e.g. SharePoint).

    NOTE: Consider checking if current file is the same as file in href
    to check if the link is in-file or f2f.
    """
    if fragment and not filename:
        return len(href) == len(fragment) + 1  # href is just "#fragment"
    return filename != "" and fragment != ""


def _find_ref_targets(
    docstate: DocumentState, href: str, fn: str, fragment: str
) -> list[RefTarget]:
    """
    Find RefTarget objects for a given anchor tag.
    It relies on the fact that in DOCX, a target reference identifier is unique,
    but only inside the same DOCX file. Therefore, we have to find a RefTarget
    linked to some source document (i.e. a document before eventual  split
    into multiple chapters).
    """
    is_internal = _is_internal(href, fn, fragment)
    if not is_internal:
        return []  # external
    rt_all: list[RefTarget] = docstate.__dict__.get("ref_targets", [])
    if is_internal and fn == "":
        # internal in-file reference
        print("TEMP", [rt for rt in rt_all if rt.fragment == fragment])

        return [
            rt
            for rt in rt_all
            if str(rt.fm_key) == str(docstate.key) and rt.fragment == fragment
        ]
    elif is_internal and fn != "":
        # internal in-file or f2f reference, check by name where to look for
        print("TEMP", [rt for rt in rt_all if rt.fragment == fragment])
        return [rt for rt in rt_all if rt.fm_key.name == fn and rt.fragment == fragment]
