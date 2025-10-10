import bs4

from src._common.metadata import DocumentMetadata
from src._common.keys import KeyPath
from src._common.state import DocumentState

# from src._common.models import Ref
from src.preparer.refs import (
    is_reference,
    prepare_references,
)
from src.preparer.targets import (
    is_caption,
    is_header,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    _get_target_label,
    _create_pre_elem_for_target_label,
)


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
