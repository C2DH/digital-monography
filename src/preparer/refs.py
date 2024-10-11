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
