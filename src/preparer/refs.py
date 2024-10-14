import bs4
import copy
import secrets
import string
import typing as t

try:
    from metadata import DocumentMetadata, TargetDatapoint
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, TargetDatapoint


def handle_targets_in_caption(
    html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    for caption in html_soup.find_all("p", {"class": "dgt-mon-caption"}):
        a = _extract_anchor_tag(html_soup, caption)
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

        _replace_data_tag(caption, None, "", a["id"])
        target = TargetDatapoint(
            full_id=a["id"],
            html="".join(str(elem) for elem in ref_stack),
            text=_get_plain_text_numbering(ref_stack),
        )
        metadata.add_target(target)
        _wrap_caption_contents_into_anchor_tag(caption, a)

    return html_soup


def _extract_anchor_tag(
    html_soup: bs4.BeautifulSoup, caption: bs4.element.Tag
) -> bs4.element.Tag:
    """
    Return an anchor tag like `<a id="_Ref178606187">`
    or `<a id="_Unref723089458">` if a caption had no bookmark
    extracted from a caption (after this func anchor is not in caption).
    In later functs, the contents of anchor tag will be wrapped into this anchor.
    """
    a = caption.find("a", id=True)
    if a is None:
        a = html_soup.new_tag("a")
        a_id = "".join(secrets.choice(string.digits) for i in range(9))
        a["id"] = "_Unref" + a_id
    else:
        # a_id = a["id"]
        a = a.extract()
    return a


def _get_plain_text_numbering(ref_stack: list[bs4.element.PageElement]) -> str:
    res = ""
    for el in ref_stack:
        if hasattr(el, "string"):
            res += el.string
        else:
            res += str(el)
    return res


def _wrap_caption_contents_into_anchor_tag(
    caption: bs4.element.Tag, a: bs4.element.Tag
) -> None:
    """
    Wrap caption contents into anchor tag
    so simplified `<p><a id="_Ref178606187"><a/>XXX</p>`
    will become `<p><a id="_Ref178606187">XXX<a/></p>`
    """
    contents = copy.copy(caption.contents)
    for el in contents:
        a.append(el)
    caption.contents = []
    caption.insert(0, a)


class SplitResult:
    """
    Splits link/cross-reference target into parts.
    Based on urllib.parse.urlsplit()
    """

    _scheme_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-."
    _unsafe_url_bytes_to_remove = ["\t", "\r", "\n"]

    def __init__(self, url: str, scheme: str = ""):
        scheme, netloc, path, query, fragment = self._urlsplit(url, scheme)
        self.scheme: str = scheme
        self.netloc: str = netloc
        self.path: str = path
        self.query: str = query
        self.fragment: str = fragment

    def _urlsplit(self, url: str, scheme: str) -> tuple[str, str, str, str, str]:
        """
        Splits url into the following parts:
            <scheme>://<net_loc>/<path>;<params>?<query>#<fragment>
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

    def is_external_url(self) -> bool:
        """E.g. 'https://example.com'"""
        return all([self.scheme, self.netloc])

    def is_cross_file_reference(self) -> bool:
        """E.g. 'filename.docx#Heading'"""
        if self.is_external_url():
            return False
        return all([self.fragment, self.path])

    def is_inner_reference(self) -> bool:
        """E.g. '#Heading'"""
        return self.is_external_url() == False and self.fragment and not self.path

    def __str__(self) -> str:
        return f"SplitResult(scheme={self.scheme}, netloc={self.netloc}, path={self.path}, query={self.query}, fragment={self.fragment})"
