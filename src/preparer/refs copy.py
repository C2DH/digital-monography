import bs4
import copy
import secrets
import string
import typing as t

try:
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata


def add_id_to_captions_without_bookmarks(
    html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    for caption in html_soup.find_all("p", {"class": "dgt-mon-caption"}):
        print("-" * 25)
        a = _extract_anchor_tag(html_soup, caption)

        # data_tags = caption.find_all("data", value=True)
        # for data_tag in data_tags:

        # TODO:
        # Here is a good place to replace static numbering with dynamic template
        # caption_as_str = str(caption)
        # if ":" in caption_as_str:
        #     match = re.search(r">\s*(\w+)\s+([a-zA-Z0-9.,;\-]+):", caption_as_str)
        #     cap_type, cap_no = match.group(1), match.group(2)
        #     print("cap_type", cap_type)
        #     print("cap_no", cap_no)

        contents = copy.copy(caption.contents)
        print("contents", contents)
        print("[type(c) for c in contents]", [type(c) for c in contents])
        print("[len(c) for c in contents]", [len(c) for c in contents])
        print('a.get("id")', a.get("id"))
        # if len(caption.contents) > 2:
        #     print("dir(caption)", dir(caption))
        #     raise Exception(
        #         ", ".join(repr(c) for c in caption)
        #         + "||| Names: ["
        #         + ", ".join(str(c.name) for c in caption)
        #         + "]"
        #     )

        ref_stack = []
        for el in contents:
            a.append(el)
        # for i in range(len(contents)):
        #     prev = contents[i - 1] if i > 0 else None
        #     curr = contents[i]
        #     nxt = contents[i + 1] if i >= len(contents) else None

        #     if isinstance(curr, bs4.element.Tag) and curr.name == "data":
        #         curr.replace_with("Something else")

        #     a.append(curr)
        caption.contents = []
        caption.insert(0, a)
    return html_soup


# def _replace_data_tag(
#     tag: bs4.element.PageElement,
#     ref_stack: list[bs4.element.PageElement],
#     first_data: t.Optional[bs4.element.Tag],
#     in_between: t.Optional[bs4.element.PageElement],
# ) -> None:
#     for child in tag.children:
#         if child.name == "data" and first_data is None:
#             first_data = child
#             # replace string
#             child.replace_with("YYYYYYYYYYYYYYY")
#             # child.string.replace_with("XXXXXXXXXXXXXXXX")
#             ref_stack.append(child)
#         elif child.name == "data":
#             ref_stack.append(child)
#             # extract child
#             # if in between : extract
#         # if in between in siblings: save as variable
#         _replace_data_tag(child, ref_stack, first_data, in_between)


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
