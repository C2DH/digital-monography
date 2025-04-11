import pathlib
import bs4
import docutils.nodes
import re
import secrets
import string
import functools
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
        CLS_DIGITAL_ONLY,
        CLS_PAPER_ONLY,
    )
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
        CLS_DIGITAL_ONLY,
        CLS_PAPER_ONLY,
    )


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


# targets ############


def prepare_ref_targets_in_headers(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    headers: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for tag in headers:
        tag: bs4.element.Tag
        anchors = []
        link = None
        for child in tag.children:
            if child.name == "a":
                target_tag = html_soup.new_tag("pre")
                link = LinkMystifier()
                link.set_filepath(metadata.filepath)
                link.set_from_id(child["id"])
                target_tag.string = link.mystify_target()
                tag.insert_before(target_tag)
                anchors.append(child)
                is_digital, is_paper = _get_isdigital_and_ispaper(tag, "")
                target = TargetDatapoint(
                    pk=link.id,
                    html=str(tag),
                    # text=link.id,
                    text=tag.text,
                    elem=str(tag),
                    item_type="heading",
                    is_digital=is_digital,
                    is_paper=is_paper,
                    prefix="",
                    file_count=metadata.get_chapter_number(),
                    prev_item_num=None,
                )
                metadata.add_target(target)
        h_lvl = "".join(ch for ch in tag.name if ch.isdigit())
        heading = HeadingDatapoint(
            file_name=metadata.filepath.name if metadata.filepath else "",
            text=tag.text,
            target=link.fragment if link else "",
            word_count=metadata.word_count,
            char_count=metadata.char_count,
            level=h_lvl,
            elem=str(tag),
        )
        metadata.add_heading(heading)
        for a in anchors:
            a.extract()
    return html_soup


def prepare_ref_targets_in_captions(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    captions: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for caption in captions:
        anchors = _extract_anchor_tags(html_soup, caption)
        item_type = _get_item_type(caption)
        unique_id = []
        ref_stack = []

        def _replace_data_tag(
            tag: bs4.element.PageElement,
            prev: t.Optional[bs4.element.PageElement],
            sep: str,
            a_id: str,
        ) -> None:
            """
            Recurse over the caption's elements to replace bookmarks
            e.g. `<data value=" SEQ Figure \\* ARABIC ">1</data>`
            with `{{ _Ref123456789 }}`, incl. numbering separated with a char.
            Replace the n-th
            """
            if not hasattr(tag, "children"):
                return
            for child in tag.children:
                if child.name == "data" and not ref_stack:
                    # handle 1-st <data> tag
                    escaped_id = (
                        a_id.replace("-", "")
                        .replace(".", "")
                        .replace("#", "")
                        .replace("_", "")
                    )
                    child.replace_with("{{ %s }}" % escaped_id)
                    unique_id.append(escaped_id)
                    sep = ""
                    ref_stack.append(child)
                elif child.name == "data":
                    # handle separator
                    if len(sep) > 0 and len(sep) < 3:
                        prev.extract()
                        ref_stack.append(sep)
                    # handle n-th <data> tag to the stack
                    ref_stack.append(child)
                    child.extract()
                elif prev and prev.name == "data":
                    sep += child.string
                prev = child
                _replace_data_tag(child, prev, sep, a_id)

        link = LinkMystifier()
        link.set_filepath(metadata.filepath)
        link.set_from_id(anchors[0]["id"])
        _replace_data_tag(caption, None, "", link.id)

        # TODO: maybe there should be some id for the caption
        # to group bookmarks that relate to the same object
        # breakpoint()
        for a in anchors:
            link = LinkMystifier()
            link.set_filepath(metadata.filepath)
            link.set_from_id(a["id"])
            identifier = link.id.replace("-", "") if not unique_id else unique_id[0]
            is_digital, is_paper = _get_isdigital_and_ispaper(caption, identifier)
            # plain_text_num = _get_plain_text_numbering(ref_stack)
            seq = TargetDatapoint.parse_ref_stack(ref_stack)
            target = TargetDatapoint(
                # html="".join(str(elem) for elem in ref_stack),
                pk=link.id,
                html=seq["html"],
                text=seq["plain_text_num"],  # calc from ref_stack
                elem=str(caption),
                item_type=seq["item_type"],
                is_digital=is_digital,  # calc from caption and identifier
                is_paper=is_paper,  # calc from caption and identifier
                file_count=metadata.get_chapter_number(),
                prefix=seq["prefix"],  # calc from ref_stack
                prev_item_num=seq["prev_item_num"],  # calc from ref_stack
            )
            metadata.add_target(target)
            if unique_id and metadata.get_substitution(unique_id[0]) is None:
                metadata.add_substitution(
                    SubstitutionDatapoint(
                        pk=unique_id[0],
                        was=target.text,
                        placeholder=target.pk,
                        # placeholder=unique_id[0],
                        # item_type=item_type,
                        item_type=target.item_type,
                        is_digital=is_digital,
                        is_paper=is_paper,
                        file_count=metadata.get_chapter_number(),
                        # new
                        target_fn=None,
                        prefix=target.prefix,
                        prev_item_num=target.prev_item_num,
                    )
                )
            target_tag = html_soup.new_tag("pre")
            target_tag.string = link.mystify_target()
            try:
                caption.insert_before(target_tag)
            except ValueError:
                caption.insert(0, target_tag)
    return html_soup


def _extract_anchor_tags(
    html_soup: bs4.BeautifulSoup, caption: bs4.element.Tag
) -> list[bs4.element.Tag]:
    """
    Return an anchor tag like `<a id="_Ref178606187">`
    or `<a id="_Unref723089458">` if a caption had no bookmark
    extracted from a caption (after this func anchor is not in caption).
    In later functs, the contents of anchor tag will be wrapped into this anchor.
    """
    anchors = caption.find_all("a", id=True)
    if not anchors:
        a = html_soup.new_tag("a")
        a_id = "".join(secrets.choice(string.digits) for i in range(9))
        a["id"] = "_Unref" + a_id
        return [a]
    else:
        for a in anchors:
            a = a.extract()
    return anchors


def _get_item_type(caption: bs4.element.Tag) -> str:
    caption_match = re.match(r"^\s*(\w+) (\d+)", caption.text)
    if caption_match is not None:
        item = caption_match.group(1)
        item = item.lower() if item else item
    else:
        return CAPTION_ITEM_TYPE_OTHER
    item_types_mapping = {
        "fig": CAPTION_ITEM_TYPE_FIGURE,
        "figure": CAPTION_ITEM_TYPE_FIGURE,
        "table": CAPTION_ITEM_TYPE_TABLE,
        "tbl": CAPTION_ITEM_TYPE_TABLE,
        "graph": CAPTION_ITEM_TYPE_GRAPH,
    }
    if item not in item_types_mapping.keys():
        return CAPTION_ITEM_TYPE_OTHER
    return item_types_mapping[item]


# def _get_plain_text_numbering(ref_stack: list[bs4.element.PageElement]) -> str:
#     res = ""
#     for el in ref_stack:
#         if hasattr(el, "string"):
#             res += el.string
#         else:
#             res += str(el)
#     return res


def _get_isdigital_and_ispaper(caption: bs4.Tag, identifier: str) -> tuple[bool, bool]:
    css_classes = [
        tag.get("class", [])
        for tag in caption.descendants
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


def prepare_ref_targets_in_footnotes(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    footnotes: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for li_tag in footnotes:
        li_tag: bs4.element.Tag
        footnote = FootnoteMystifier()
        footnote.set_filepath(metadata.filepath)
        footnote.from_target(li_tag["id"])
        li_tag["id"] = footnote.id
        for tag in li_tag.descendants:
            if isinstance(tag, bs4.element.Tag) and tag.attrs.get(
                "href", ""
            ).startswith("#footnote-ref-"):
                tag["href"] = footnote.href
                break
    return html_soup


# references ############


def prepare_references(
    html_soup: bs4.BeautifulSoup,
    metadata: DocumentMetadata,
    references: list[bs4.element.Tag],
) -> bs4.BeautifulSoup:
    for a_tag in references:
        a_tag: bs4.element.Tag
        if _is_ref_footnote(a_tag):
            footnote = FootnoteMystifier()
            footnote.set_filepath(metadata.filepath)
            footnote.from_ref(a_tag["id"])
            a_tag["href"] = footnote.href
            a_tag["id"] = footnote.id
            a_tag.string = footnote.string
        elif _is_target_footnote(a_tag):
            pass
        else:
            if _check_if_link_marked_as_paper_only(a_tag):
                # a_tag.extract()
                tag_class = a_tag.get("class", [])
                tag_class.append(CLS_PAPER_ONLY)
                a_tag["class"] = tag_class

            link = LinkMystifier()
            link.set_filepath(metadata.filepath)
            link.set_from_href(a_tag["href"])
            target = metadata.get_target(link.id) if link.is_inner_reference() else None
            link_text = link.make_text(a_tag.text, target)
            link_dest = link.make_destination()
            prev_string = a_tag.string
            prev_href = a_tag["href"]
            a_tag.string = link_text
            a_tag["href"] = link_dest
            ref = RefDatapoint(
                target_id=target.pk if target else "",
                fn=metadata.filepath.name,
                text=link_text,
                href=link_dest,
                prev_string=prev_string,
                prev_href=prev_href,
                elem=str(a_tag.parent),
            )
            metadata.add_ref(ref)
            if link.unique_id and metadata.get_substitution(link.unique_id) is None:
                # get chapter number from the href if f2f else number from current file
                target_chapter_number = (
                    metadata.get_chapter_number(link.path)
                    if link.path and link.is_cross_file_reference()
                    else metadata.get_chapter_number()
                )
                target_fn = (
                    link.path if link.path and link.is_cross_file_reference() else None
                )
                metadata.add_substitution(
                    SubstitutionDatapoint(
                        pk=link.unique_id,
                        was=link.text_to_replace,
                        # placeholder=link.unique_id,
                        placeholder=link.id,
                        item_type="ref",
                        is_digital=None,
                        is_paper=None,
                        target_fn=target_fn,
                        file_count=target_chapter_number,
                        prefix="",
                        prev_item_num=None,
                    )
                )
    return html_soup


def _is_ref_footnote(a_tag: bs4.element.Tag) -> bool:
    if "footnote" not in a_tag["href"]:
        return False
    return bool(a_tag.attrs.get("id", "").startswith("footnote-ref-"))


def _is_target_footnote(a_tag: bs4.element.Tag) -> bool:
    return bool(a_tag.attrs.get("href", "").startswith("#footnote-ref-"))


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
        if "XXX" in tag_text:
            self.text_to_replace = "XXX"
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


class FootnoteMystifier:
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

    # TODO: handle endnotes the same way as footnotes

    def __init__(self):
        self.filepath: t.Optional[KeyPath] = None
        self.href: str = ""
        self.id: str = ""
        self.string: str = ""

    def set_filepath(self, fn: t.Optional[KeyPath]) -> None:
        self.filepath = fn

    def _get_unique_id(self, old_id: str) -> str:
        return docutils.nodes.make_id(f"fn-{self.filepath.stem}-{old_id}")

    def from_ref(self, a_id: str):
        assert a_id.startswith("footnote-ref-") == True
        unique_id = self._get_unique_id(a_id[len("footnote-ref-") :])
        self.href = f"#footnote-{unique_id}"
        self.string = f"[{unique_id}]"
        # only for going back from target to ref in html, irrelevant in md
        self.id = f"footnote-ref-{unique_id}"

    def from_target(self, li_id: str):
        assert li_id.startswith("footnote-ref-") == False
        assert li_id.startswith("footnote-") == True
        unique_id = self._get_unique_id(li_id[len("footnote-") :])
        self.id = f"footnote-{unique_id}"
        # only for going back from target to ref in html, irrelevant in md
        self.href = f"#footnote-ref-{unique_id}"

    def __str__(self) -> str:
        return f"FootnoteMystifier(href={self.href}, id={self.id})"
