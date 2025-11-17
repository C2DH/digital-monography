import bs4
import docutils.nodes
import xxhash
import uuid

from src._common.constants import (
    CLS_PAPER_ONLY,
    REF_STRING_PREFIX,
    REF_PREFIX,
)
from src._common.metadata import (
    DocumentMetadata,
)
from src._common.models import Substitution, Ref
from src._common.state import DocumentState


def is_reference(tag: bs4.element.Tag) -> bool:
    # "a", href=True
    return bool(tag.name == "a" and tag.attrs.get("href"))


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

    Since preparer microservice works on per-document basis,
    we don't have access to other documents to link f2f references with targets.
    Hence, this function
        1) registers references in the docstate,
        2) modifies the HTML by adding placeholders for substitutions
           to be handled in later stages, when we have access to all documents.

    Note this replaces the whole string of the <a> tag with a placeholder.
    """
    # for chpt in docstate.__dict__.get("chapters"):
    #     print("chapter in docstate", chpt)

    for a_tag in references:
        if _is_ref_footnote(a_tag) or _is_target_footnote(a_tag):
            # handled in footnotes.py
            continue
        _mark_paper_only_tag(a_tag)
        prev_href = a_tag["href"]
        fn, fragment = _get_fn_and_fragment_from_href(a_tag["href"])
        is_internal = _is_internal(a_tag["href"], fn, fragment)
        # ref_targets = _find_ref_targets(docstate, fn, fragment)
        # print("ref_targets", ref_targets)
        if not is_internal:
            ref = Ref(
                loc=docstate.key,
                target_id="",
                fn=docstate.key.name if docstate.key else "",
                text=a_tag.text,
                href=a_tag["href"],
                prev_string=a_tag.string if a_tag.string is not None else "",
                prev_href=a_tag["href"],
                elem=str(a_tag.parent),
            )
            docstate.add(ref)
            continue
        ref_pk = uuid.uuid4().hex
        # get text to put into [text](...)
        # link_text = _make_text(a_tag.text, ref_pk)
        # get dest to put into [...](destination)
        # link_dest = _make_destination() # nah, just ref_pk

        # print("prev_string", prev_string)
        # print("a_tag.string", a_tag.string)
        # print('a_tag["href"]', a_tag["href"])
        # print(
        #     "a_tag > before string replacement", a_tag
        # )  # <a class="dgt-mon-paper-only" href="#figForPaper"><span class="dgt-mon-paper-only">link to figForPaper bookmark</span></a>
        prev_string = a_tag.string if a_tag.string is not None else ""
        prev_href = a_tag["href"]
        unique_id = docutils.nodes.make_id(
            f"{REF_PREFIX}-{docstate.key.stem}-{prev_href}"
        )
        THE_MOST_IMPORTANT_2_LINES = """
        a_tag.string = r"{{ " + REF_STRING_PREFIX + ref_pk + r" }}"  # placeholder
        this_seems_unnecessary = 'a_tag["href"] = ref_pk'
        """
        # print(
        #     "a_tag > after string replacement", a_tag
        # )  # <a class="dgt-mon-paper-only" href="#f-05-conditional-rendering-figforpaper">link to figForPaper bookmark</a>
        # ref = RefDatapoint(
        #     target_id=target.pk if target else "",
        #     fn=metadata.filepath.name,
        #     text=link_text,
        #     href=link_dest,
        #     prev_string=prev_string,
        #     prev_href=prev_href,
        #     elem=str(a_tag.parent),
        # )
        # print("RefDatapoint", ref)
        # metadata.add_ref(ref)
        data = Ref(
            loc=docstate.key,
            target_id="",
            fn=docstate.key.name if docstate.key else "",
            text=a_tag.string,
            # text=r"{{ " + ref_pk + r" }}",
            href=ref_pk,
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
        # print("link.unique_id", link.unique_id)  # f05conditionalrenderingref193102988
        # print(
        #     "metadata.get_substitution(link.unique_id)",
        #     metadata.get_substitution(link.unique_id),
        # )
        # TODO: get substitution from docstate
        # if link.unique_id and metadata.get_substitution(link.unique_id) is None:
        if unique_id and docstate.get("substitutions", unique_id) is None:
            data = Substitution(
                loc=docstate.key,
                pk=unique_id,
                was="",  # Previously this was link.text_to_replace, but maybe it will be easier to handle it at builder stage?
                # placeholder=link.unique_id,
                placeholder=ref_pk,
                item_type="ref",
                is_digital=None,
                is_paper=None,
                location=metadata.filepath,
                target_fn="",
                # target_fn=target_fn,
                file_count=None,  # Prev this was metadata.get_chapter_number(link.path) if link.path and link.is_cross_file_reference() else metadata.get_chapter_number()
                prefix="",
                prev_item_num=None,
                hash=_hash_html(a_tag),
            )
            # print("S>", data.model_dump())
            docstate.add(data)
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


def _hash_html(html_elem: str | bs4.PageElement, seed: int = 0) -> str:
    """
    Returns 16-char hex lowercase string using 64-bit arithmetic operation.
    For example, for string "<h2>Heading</h2>" it returns "35110f86aeaa2f35".
    """
    if isinstance(html_elem, bs4.PageElement):
        html_elem = str(html_elem)
    return xxhash.xxh64(html_elem, seed=seed).hexdigest()
