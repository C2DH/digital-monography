import bs4

from src._common.metadata import DocumentMetadata, TargetDatapoint
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src._common.models import Ref
from src.preparer.refs import (
    # is_caption,
    # is_header,
    is_reference,
    # prepare_ref_targets_in_headers,
    # prepare_ref_targets_in_captions,
    prepare_references,
    LinkMystifier,
)
from src.preparer.targets import (
    is_caption,
    is_header,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    _get_target_label,
    _create_pre_elem_for_target_label,
)

# targets in headers


def test_targets_in_headers__heading_reference_targets():
    sample_html = '<h1><a id="_Heading">XXX</h1>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_id(bs.h1.a["id"])
    assert link.mystify_target() == "(f-heading)="
    assert link.make_destination() == "#f-heading"


def test_targets_in_headers__heading_crossref_targets_were_added():
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
    assert len(pres) == 3
    assert pres[0].text == "(f-file-heading)="
    assert pres[1].text == "(f-file-heading-2)="
    assert pres[2].text == "(f-file-heading-3)="
    assert str(bs).startswith(
        "<pre>(f-file-heading)=</pre>"
        "<pre>(f-file-heading-2)=</pre>"
        "<h1>Heading</h1>"
        "<h2>Heading level 2</h2>"
        "<pre>(f-file-heading-3)=</pre>"
        "<h3>Heading level 3</h3>"
    )


def test_targets_in_headers__corresponding_href_and_id():
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
    references = []
    classifiers = [
        (is_reference, references),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_ref_targets_in_headers(bs, metadata, dstate, headers)
    bs = prepare_references(bs, metadata, dstate, references)
    pre = bs.find("pre")
    assert pre.text == "(f-file-heading)="
    anchors = bs.find_all("a", href=True)
    assert anchors[0]["href"] == "#f-file-heading"
    assert anchors[1]["href"] == "./other_file.md#f-other-file-heading"


def test_targets_in_headers__refs_and_targets_written_to_metadata():
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
    references = []
    classifiers = [
        (is_reference, references),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_ref_targets_in_headers(bs, metadata, dstate, headers)
    bs = prepare_references(bs, metadata, dstate, references)
    assert dstate.len("targets") == 3
    assert dstate.len("refs") == 2
    assert dstate.get("targets", "f-file-heading") is not None
    assert dstate.get("targets", "f-file-heading-2") is not None
    assert dstate.get("targets", "f-file-heading-3") is not None
    ref1 = metadata.get_ref(attrib="href", val="#f-file-heading")
    print("ref1", ref1)
    ref: Ref = dstate.get("refs", val="#f-file-heading", attrib="href")
    print("ref", ref)
    assert ref is not None
    assert ref.target_id != "", "Why is the target_id empty???"
    assert ref.target_id == "f-file-heading"
    assert 1 == 666
    ref = metadata.get_ref(attrib="href", val="./other_file.md#f-other-file-heading")
    # ref: Ref = dstate.get(
    #     "refs", val="./other_file.md#f-other-file-heading", attrib="href"
    # )
    assert ref is not None
    assert ref.target_id == ""  # no target found since it is in another file


# targets in captions


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
    assert pre.text == "(f-file-ref178606189)="
    assert pre.find_next_sibling() == captions[0]
    target = metadata.get_target("f-file-ref178606189")
    assert target.text == "1"


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
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, dstate, captions)
    pres = bs.find_all("pre")
    assert len(pres) == 2
    assert pres[0].text == "(f-file-ref178606187)="
    assert pres[1].text == "(f-file-ref178606188)="
    assert str(bs) == (
        "<pre>(f-file-ref178606187)=</pre>"
        "<pre>(f-file-ref178606188)=</pre>"
        '<p class="dgt-mon-caption">'
        "<strong>Figure {{ ffileref178606187 }}:</strong>"
        # "<strong>Figure {{ f-file-ref178606187 }}:</strong>"
        " Duplicated bookmarks.</p>"
    )
    target = metadata.get_target("f-file-ref178606187")
    assert target.text == "3"
    target = metadata.get_target("f-file-ref178606188")
    assert target.text == "3"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0].was == "3"
    assert metadata.substitutions[0].pk == "ffileref178606187"
    assert metadata.substitutions[0].placeholder == "f-file-ref178606187"
    # assert metadata.substitutions[0]["placeholder"] == "f-file-ref178606187"


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
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, dstate, captions)
    assert (
        captions[0].text
        == "Figure {{ ffileref178606189 }}: Complex numbering with separator."
    )
    # assert (
    #     captions[0].text
    #     == "Figure {{ f-file-ref178606189 }}: Complex numbering with separator."
    # )
    target = metadata.get_target("f-file-ref178606189")
    assert target.text == "5.B"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0].was == "5.B"
    assert metadata.substitutions[0].pk == "ffileref178606189"
    assert metadata.substitutions[0].placeholder == "f-file-ref178606189"


def test_targets_in_captions__replace_roman_numbering_in_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ROMAN ">IV</data>:</strong>'
        " Roman numbering.</p>"
    )  # IV -> {{ file___Ref178606189 }}
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("./tmp/sth/file.docx")
    dstate = DocumentState(key)
    metadata = DocumentMetadata(key)
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, dstate, captions)
    assert captions[0].text == "Figure {{ ffileref178606189 }}: Roman numbering."
    # assert captions[0].text == "Figure {{ f-file-ref178606189 }}: Roman numbering."
    target = metadata.get_target("f-file-ref178606189")
    assert target.text == "IV"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0].was == "IV"
    assert metadata.substitutions[0].pk == "ffileref178606189"
    assert metadata.substitutions[0].placeholder == "f-file-ref178606189"


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
    assert captions[0].text == "Figure {{ ffileref178606190 }}: Caption with a link."
    # assert captions[0].text == "Figure {{ f-file-ref178606190 }}: Caption with a link."
    target = metadata.get_target("f-file-ref178606190")
    assert target.text == "2"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0].was == "2"
    assert metadata.substitutions[0].pk == "ffileref178606190"
    assert metadata.substitutions[0].placeholder == "f-file-ref178606190"


# LinkMystifier attributes


def test_is_external_url():
    sample_html = '<a href="https://c2dh.uni.lu/">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.uri == "https://c2dh.uni.lu/"
    assert link.scheme == "https"
    assert link.netloc == "c2dh.uni.lu"
    assert link.path == "/"
    assert link.query == ""
    assert link.fragment == ""
    assert link.is_external_url() == True
    assert link.is_cross_file_reference() == False
    assert link.is_inner_reference() == False


def test_is_external_url_with_path():
    sample_html = '<a href="http://c2dh.uni.lu/people/">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.uri == "http://c2dh.uni.lu/people/"
    assert link.scheme == "http"
    assert link.netloc == "c2dh.uni.lu"
    assert link.path == "/people/"
    assert link.query == ""
    assert link.fragment == ""
    assert link.is_external_url() == True
    assert link.is_cross_file_reference() == False
    assert link.is_inner_reference() == False


def test_is_inner_reference():
    sample_html = '<a href="#_Ref177042490">Figure <strong>1</strong></a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.uri == "#_Ref177042490"
    assert link.scheme == ""
    assert link.netloc == ""
    assert link.path == ""
    assert link.query == ""
    assert link.fragment == "f-ref177042490"
    assert link.is_external_url() == False
    assert link.is_cross_file_reference() == False
    assert link.is_inner_reference() == True


def test_is_cross_file_reference():
    sample_html = '<a href="filename.docx#h-target">see Chapter 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.scheme == ""
    assert link.netloc == ""
    assert link.path == "filename.docx"
    assert link.query == ""
    assert link.fragment == "f-h-target"
    assert link.is_external_url() == False
    assert link.is_cross_file_reference() == True
    assert link.is_inner_reference() == False


def test_is_not_external_url_nor_cross_file_ref_nor_inner_ref():
    sample_html = '<a href="example.com">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.is_external_url() == False
    assert link.is_cross_file_reference() == False
    assert link.is_inner_reference() == False


# LinkMystifier methods


def test_markownify_anchor_if_is_external_url():
    sample_html = '<a href="https://c2dh.uni.lu">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "the website"
    assert link.make_destination() == "https://c2dh.uni.lu"


def test_markownify_anchor_if_is_external_url_with_path():
    sample_html = '<a href="http://c2dh.uni.lu/people/">a website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "a website"
    assert link.make_destination() == "http://c2dh.uni.lu/people/"


def test_markownify_anchor_if_is_inner_reference__complex_a_tag():
    sample_html = '<a href="#_Ref177042490">Figure <strong>1</strong></a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    target = TargetDatapoint(
        pk="_Ref177042490",
        html='<data value=" SEQ Figure \\* ARABIC ">1</data>',
        text="1",
        elem=str(bs.a),
        item_type="figure",
        file_count=None,
        prefix="",
        prev_item_num=1,
        is_digital=None,
        is_paper=None,
        filename="",
        fragment="_Ref177042490",
    )
    assert link.make_text(bs.a.text, target) == r"Figure {{ fref177042490 }}"
    # assert link.make_text(bs.a.text, target) == r"Figure {{ f-ref177042490 }}"
    assert link.make_destination() == "#f-ref177042490"
    assert link.text_to_replace == "1"
    assert link.unique_id == "fref177042490"
    # assert link.unique_id == "f-ref177042490"


def test_markownify_anchor_if_is_inner_reference__simple_a_tag():
    sample_html = '<a href="#_Ref177042491">Figure 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    target = TargetDatapoint(
        pk="_Ref177042491",
        html='<data value=" SEQ Figure \\* ARABIC ">2</data>',
        text="2",
        elem=str(bs.a),
        item_type="figure",
        file_count=None,
        prefix="",
        prev_item_num=2,
        is_digital=None,
        is_paper=None,
        filename="",
        fragment="_Ref177042491",
    )
    assert link.make_text(bs.a.text, target) == r"Figure {{ fref177042491 }}"
    # assert link.make_text(bs.a.text, target) == r"Figure {{ f-ref177042491 }}"
    assert link.make_destination() == "#f-ref177042491"
    assert link.text_to_replace == "2"
    assert link.unique_id == "fref177042491"
    # assert link.unique_id == "f-ref177042491"


def test_markownify_anchor_if_is_cross_file_reference():
    sample_html = '<a href="filename.docx#h-target">see Chapter 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == r"see Chapter {{ filenamedocxfhtarget }}"
    # assert link.make_text(bs.a.text) == r"see Chapter {{ filename.docx#f-h-target }}"
    assert link.make_destination() == "./filename.md#f-h-target"
    assert link.text_to_replace == "2"
    assert link.unique_id == "filenamedocxfhtarget"
    # assert link.unique_id == "filename.docx#f-h-target"


def test_markownify_anchor_if_is_cross_file_reference__nothing_to_replace():
    sample_html = '<a href="filename.docx#h-target">see heading in other file</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "see heading in other file"
    assert link.make_destination() == "./filename.md#f-h-target"


def test_markownify_anchor_if_is_not_external_url_nor_cross_file_ref_nor_inner_ref():
    sample_html = '<a href="example.com">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "the website"
    assert link.make_destination() == "example.com"


def test_target_label_and_create_pre_elem():
    sample_html = '<a id="_Heading"></a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    key = KeyPath("a_slug") / "01_a.docx"
    target_label = _get_target_label(key, bs.a)
    assert target_label == "f-01-a-heading"
    target_tag = _create_pre_elem_for_target_label(bs, target_label)
    assert target_tag.name == "pre"
    assert target_tag.string == "(f-01-a-heading)="
    bs.a.insert_before(target_tag)
    assert str(bs) == '<pre>(f-01-a-heading)=</pre><a id="_Heading"></a>'
