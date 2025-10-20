import bs4
import pytest

from src._common.models import Substitution, Target
from src._common.metadata import DocumentMetadata
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src.preparer.references import (
    _get_fn_and_fragment_from_href,
    _is_internal,
)


from src.preparer.targets import (
    is_caption,
    is_header,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
)


# TODO: replace tests in refs_test.py with these


def test_insert_just_one_target_label_per_heading():
    sample_html = (
        # '<!-- targets -->'
        '<h1><a id="_Heading"></a><a id="heading_2"></a>Heading</h1>'
        "<h2>Heading level 2</h2>"
        '<h3><a id="heading_3"></a>Heading level 3</h3>'
        # '<!-- references -->'
        '<p>A <a href="#_Heading">link</a>.</p>'
        '<p>B <a href="other_file.docx#_Heading">link</a>.</p>'
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    headers = [node for node in bs.children if is_header(node)]
    bs = prepare_ref_targets_in_headers(bs, metadata, dstate, headers)
    pres = bs.find_all("pre")
    assert len(pres) == 2
    assert pres[0].text == "(b5cc767554b7a737)="
    assert pres[1].text == "(a320ce48caabeb5c)="
    assert str(bs).startswith(
        "<pre>(b5cc767554b7a737)=</pre>"
        "<h1>Heading</h1>"
        "<h2>Heading level 2</h2>"
        "<pre>(a320ce48caabeb5c)=</pre>"
        "<h3>Heading level 3</h3>"
    )


def test_targets_in_captions__insert_pre_tag_before_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        r'Figure <data value=" SEQ Figure \* ARABIC ">1</data>: No bold.'
        "</p>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, dstate, captions)
    pre = bs.find("pre")
    assert pre
    assert pre.text == "(4a5f1afdd58f2af8)="
    assert pre.find_next_sibling() == captions[0]
    target: Target = dstate.get("targets", "4a5f1afdd58f2af8", "hash")
    assert target.text == "1"
    assert str(bs).startswith(
        "<pre>(4a5f1afdd58f2af8)=</pre>"
        '<p class="dgt-mon-caption">Figure {{ 4a5f1afdd58f2af8 }}: No bold.</p>'
    )


def test_targets_in_captions__duplicated_target_id():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606187"></a>'
        '<a id="_Ref178606188"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ARABIC ">3</data>'
        ":</strong> Duplicated bookmarks.</p>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    docstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, docstate, captions)
    pres = bs.find_all("pre")
    assert len(pres) == 1
    assert pres[0].text == "(53db9168dc9c72eb)="
    assert str(bs) == (
        "<pre>(53db9168dc9c72eb)=</pre>"
        '<p class="dgt-mon-caption">'
        "<strong>Figure {{ 53db9168dc9c72eb }}:</strong>"
        " Duplicated bookmarks.</p>"
    )
    target: Target = docstate.get("targets", "53db9168dc9c72eb", "hash")
    assert target.text == "3"
    assert docstate.len("substitutions") == 1
    substitution: Substitution = docstate.get(
        "substitutions", "53db9168dc9c72eb", "hash"
    )
    assert substitution.was == "3"
    assert substitution.hash == "53db9168dc9c72eb"
    assert substitution.placeholder == "53db9168dc9c72eb"


def test_targets_in_captions__replace_complex_numbering_in_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        "<strong>Figure "
        r'<data value=" STYLEREF 1 \s ">5</data><i>.</i><data value=" SEQ Equation \* ALPHABETIC \s 1 ">B</data>'
        ":</strong> Complex numbering with separator.</p>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    docstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, docstate, captions)
    assert (
        captions[0].text
        == "Figure {{ 530e400e369f7bd0 }}: Complex numbering with separator."
    )
    target: Target = docstate.get("targets", "530e400e369f7bd0", "hash")
    assert target.text == "5.B"
    assert docstate.len("substitutions") == 1
    subst: Substitution = docstate.get("substitutions", "530e400e369f7bd0", "hash")
    assert subst.was == "5.B"
    assert subst.hash == "530e400e369f7bd0"
    assert subst.placeholder == "530e400e369f7bd0"


def test_targets_in_captions__replace_roman_numbering_in_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ROMAN ">IV</data>:</strong>'
        " Roman numbering.</p>"
    )  # IV -> {{ ecec2a7dadb0859f }}
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    docstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, docstate, captions)
    assert captions[0].text == "Figure {{ ecec2a7dadb0859f }}: Roman numbering."
    target: Target = docstate.get("targets", "ecec2a7dadb0859f", "hash")
    assert target.text == "IV"
    assert docstate.len("substitutions") == 1
    subst: Substitution = docstate.get("substitutions", "ecec2a7dadb0859f", "hash")
    assert subst.was == "IV"
    assert subst.hash == "ecec2a7dadb0859f"
    assert subst.placeholder == "ecec2a7dadb0859f"


def test_targets_in_captions__link_in_caption_is_left_not_changed():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606190"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ARABIC ">2</data>'
        ":</strong> Caption with a "
        '<a href="https://example.com">link</a>.</p>'
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, dstate, captions)
    a = bs.find("a")
    assert a
    assert a["href"] == "https://example.com"
    assert a.string == "link"
    assert captions[0].text == "Figure {{ d9ba804a0d84c08d }}: Caption with a link."
    target: Target = dstate.get("targets", "d9ba804a0d84c08d", "hash")
    assert target.text == "2"
    assert dstate.len("substitutions") == 1
    subst: Substitution = dstate.get("substitutions", "d9ba804a0d84c08d", "hash")
    assert subst.was == "2"
    assert subst.hash == "d9ba804a0d84c08d"
    assert subst.placeholder == "d9ba804a0d84c08d"
    assert str(bs).startswith(
        "<pre>(d9ba804a0d84c08d)=</pre>"
        '<p class="dgt-mon-caption">'
        "<strong>Figure {{ d9ba804a0d84c08d }}:</strong> "
        'Caption with a <a href="https://example.com">link</a>.'
        "</p>"
    )


#########################################################

### new href parser

MOVED = '''
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
'''

# def _extract_filename_from_href(href: str, fragment_idx: int | None = None) -> str:
#     """
#     Extracts filename from an URI if the filename is present.
#     """
#     if fragment_idx is None:
#         # 'A fragment identifier component is indicated by the presence of a number sign ("#")'
#         # so it should always be an index of #.
#         # See https://www.rfc-editor.org/rfc/rfc3986#section-3.5
#         fragment_idx = href.index("#")
#     path = href[:fragment_idx]
#     if "." not in path:
#         return ""
#     for scheme in ["tel:", "mailto:", "sms:", "javascript:"]:
#         if path.startswith(scheme):
#             return ""
#     if "/" not in path:
#         return path
#     filename = ""
#     for i in range(len(path) - 1, -1, -1):
#         ch = path[i]
#         # if ch == ".":
#         #     suffix = path[i + 1 :]
#         if ch == "/":
#             filename = path[i + 1 :]
#             break
#     if "." not in filename:
#         return ""
#     return filename


# def _extract_fragment_from_href(href: str) -> tuple[int | None, str]:
#     """
#     Extracts fragment identifier from an URI
#     See https://www.rfc-editor.org/rfc/rfc3986#section-3.5

#     The function returns index where the fragment begins and the fragment itself.
#     E.g. "a_Fragment" from:
#         "https://unilux.sharepoint.com/personal/joe_doe/Documents/Books/book-slug/manuscript.docx#a_Fragment"
#         "./manuscript.docx#a_Fragment"

#     Calculation of the "#" index is only to avoid calling href.index("#") second time.
#     I couldn't find information about allowed characters in docx fragments in ECMA 376.
#     I noticed that Word allows only alphanumerics and underscores (except as the first char)
#     in bookmarks, so I assumed the same for OOXML fragments.
#     """
#     if "#" not in href:
#         return None, ""
#     for i in range(len(href) - 1, -1, -1):
#         ch = href[i]
#         if ch == "#":
#             fragment = href[i + 1 :]
#             if fragment[0] == "_":
#                 return None, ""  # bookmarks cannot start with an underscore
#             return i, fragment
#         elif not ch.isalnum() and ch != "_":
#             return None, ""
#     return None, ""


# raise NotImplementedError(
#     "Move extraction to refs. Maybe as a class with static methods? The point is, we need to parse href before handling refs."
# )


@pytest.mark.parametrize(
    "href,exp_fn,exp_fragment,exp_internal",
    [
        (
            "https://unilux.sharepoint.com/personal/joe_doe/Documents/Books/book-slug/manuscript.docx#a_Fragment",
            "manuscript.docx",
            "a_Fragment",
            True,
        ),
        ("manuscript.docx#a_Fragment", "manuscript.docx", "a_Fragment", True),
        ("./manuscript.docx#a_Fragment", "manuscript.docx", "a_Fragment", True),
        ("#a_Fragment", "", "a_Fragment", True),
        ("mailto:example@example.com", "", "", False),
        ("http://example.com/some/someDocument.docx", "someDocument.docx", "", False),
        ("http://example.com/some/someDocument.pdf#", "someDocument.pdf", "", False),
        ("http://example.com/home/homepage#fragment", "", "fragment", False),
    ],
)
def test_href_parser(href, exp_fn, exp_fragment, exp_internal):
    fn, fragment, is_internal = _get_fn_and_fragment_from_href(href)
    assert fn == exp_fn
    assert fragment == exp_fragment
    assert is_internal == exp_internal
