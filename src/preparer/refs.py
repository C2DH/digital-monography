import bs4
import re
import secrets
import string
import functools
import typing as t

try:
    from metadata import DocumentMetadata, TargetDatapoint, RefDatapoint
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, TargetDatapoint, RefDatapoint
    from .keys import KeyPath


def is_header(tag: bs4.element.Tag) -> bool:
    return bool(re.match(r"^h[1-6]$", tag.name))


def is_caption(tag: bs4.element.Tag) -> bool:
    # "p", {"class": "dgt-mon-caption"}
    return bool(tag.name == "p" and "dgt-mon-caption" in tag.attrs.get("class", []))


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
        for child in tag.children:
            if child.name == "a":
                target_tag = html_soup.new_tag("pre")
                link = LinkMystifier()
                link.set_filepath(metadata.filepath)
                link.set_from_id(child["id"])
                target_tag.string = link.mystify_target()
                tag.insert_before(target_tag)
                anchors.append(child)
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
                    child.replace_with("{{ %s }}" % a_id)
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
        for a in anchors:
            link = LinkMystifier()
            link.set_filepath(metadata.filepath)
            link.set_from_id(a["id"])
            target = TargetDatapoint(
                pk=link.id,
                html="".join(str(elem) for elem in ref_stack),
                text=_get_plain_text_numbering(ref_stack),
            )
            metadata.add_target(target)
            target_tag = html_soup.new_tag("pre")
            target_tag.string = link.mystify_target()
            print("target_tag.string", target_tag.string)
            caption.insert_before(target_tag)

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


def _get_plain_text_numbering(ref_stack: list[bs4.element.PageElement]) -> str:
    res = ""
    for el in ref_stack:
        if hasattr(el, "string"):
            res += el.string
        else:
            res += str(el)
    return res


# references ############


def prepare_references(
    html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata, references
) -> bs4.BeautifulSoup:
    for a_tag in references:
        a_tag: bs4.element.Tag
        # link = LinkMystifier(a_tag)
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
        metadata.add_ref(
            RefDatapoint(
                target_id=target.pk if target else "",
                text=link_text,
                href=link_dest,
                prev_string=prev_string,
                prev_href=prev_href,
            )
        )
    return html_soup


class LinkMystifier:
    """
    Translate html anchor tags to MyST/markdown link syntax.
    """

    _scheme_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-."
    _unsafe_url_bytes_to_remove = ["\t", "\r", "\n"]

    def __init__(self):
        self.filepath: t.Optional[KeyPath] = None
        self.scheme: str = ""
        self.netloc: str = ""
        self.path: str = ""
        self.query: str = ""
        self.fragment: str = ""
        ##################################
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
        self.scheme, self.netloc, self.path, self.query, self.fragment = self._urlsplit(
            href
        )

    def set_from_id(self, id: str) -> None:
        self.fragment = id

    @property
    def fragment(self) -> str:
        return self._fragment

    @fragment.setter
    def fragment(self, val: str):
        if self.path:
            self._fragment = f"{self.path}__{val}"
        if self.filepath and not self.path:
            self._fragment = f"{self.filepath.stem}__{val}"
        else:
            self._fragment = val

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
        if self.is_cross_file_reference():
            to_replace = ""
            for i in range(len(tag_text)):
                if tag_text[i].isdigit():
                    to_replace += tag_text[i]
                if to_replace and not tag_text[i].isdigit():
                    break
            replace_with = r"{{ " + self.path + "#" + self.fragment + r" }}"
            if to_replace:
                tag_text = tag_text.replace(to_replace, replace_with)
        elif self.is_inner_reference():
            if target is not None:
                to_replace = target.text
                replace_with = r"{{ " + self.fragment + r" }}"
                tag_text = tag_text.replace(to_replace, replace_with)
        return tag_text

    def __str__(self) -> str:
        return f"LinkMystifier(scheme={self.scheme}, netloc={self.netloc}, path={self.path}, query={self.query}, fragment={self.fragment})"
