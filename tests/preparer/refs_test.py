import bs4

from src.preparer.refs import (
    is_caption,
    is_header,
    is_footnote,
    is_reference,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    prepare_ref_targets_in_footnotes,
    prepare_references,
    LinkMystifier,
)
from src.preparer.metadata import DocumentMetadata, TargetDatapoint
from src.preparer.keys import KeyPath

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
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    headers = [node for node in bs.children if is_header(node)]
    bs = prepare_ref_targets_in_headers(bs, metadata, headers)
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
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    headers = [node for node in bs.children if is_header(node)]
    references = []
    classifiers = [
        (is_reference, references),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_ref_targets_in_headers(bs, metadata, headers)
    bs = prepare_references(bs, metadata, references)
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
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    headers = [node for node in bs.children if is_header(node)]
    references = []
    classifiers = [
        (is_reference, references),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_ref_targets_in_headers(bs, metadata, headers)
    bs = prepare_references(bs, metadata, references)
    assert len(metadata.targets) == 3
    assert len(metadata.refs) == 2
    assert metadata.get_target("f-file-heading") is not None
    assert metadata.get_target("f-file-heading-2") is not None
    assert metadata.get_target("f-file-heading-3") is not None
    ref = metadata.get_ref(attrib="href", val="#f-file-heading")
    assert ref is not None
    assert ref.target_id == "f-file-heading"
    ref = metadata.get_ref(attrib="href", val="./other_file.md#f-other-file-heading")
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
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, captions)
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
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, captions)
    pres = bs.find_all("pre")
    assert len(pres) == 2
    assert pres[0].text == "(f-file-ref178606187)="
    assert pres[1].text == "(f-file-ref178606188)="
    assert str(bs) == (
        "<pre>(f-file-ref178606187)=</pre>"
        "<pre>(f-file-ref178606188)=</pre>"
        '<p class="dgt-mon-caption">'
        "<strong>Figure {{ f-file-ref178606187 }}:</strong>"
        " Duplicated bookmarks.</p>"
    )
    target = metadata.get_target("f-file-ref178606187")
    assert target.text == "3"
    target = metadata.get_target("f-file-ref178606188")
    assert target.text == "3"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0]["was"] == "3"
    assert metadata.substitutions[0]["placeholder"] == "f-file-ref178606187"


def test_targets_in_captions__replace_complex_numbering_in_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        "<strong>Figure "
        r'<data value=" STYLEREF 1 \s ">5</data><i>.</i><data value=" SEQ Equation \* ALPHABETIC \s 1 ">B</data>'
        ":</strong> Complex numbering with separator.</p>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, captions)
    assert (
        captions[0].text
        == "Figure {{ f-file-ref178606189 }}: Complex numbering with separator."
    )
    target = metadata.get_target("f-file-ref178606189")
    assert target.text == "5.B"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0]["was"] == "5.B"
    assert metadata.substitutions[0]["placeholder"] == "f-file-ref178606189"


def test_targets_in_captions__replace_roman_numbering_in_caption():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606189"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ROMAN ">IV</data>:</strong>'
        " Roman numbering.</p>"
    )  # IV -> {{ file___Ref178606189 }}
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, captions)
    assert captions[0].text == "Figure {{ f-file-ref178606189 }}: Roman numbering."
    target = metadata.get_target("f-file-ref178606189")
    assert target.text == "IV"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0]["was"] == "IV"
    assert metadata.substitutions[0]["placeholder"] == "f-file-ref178606189"


def test_targets_in_captions__link_in_caption_is_left_not_changed():
    sample_html = (
        '<p class="dgt-mon-caption">'
        '<a id="_Ref178606190"></a>'
        r'<strong>Figure <data value=" SEQ Figure \* ARABIC ">2</data>'
        ":</strong> Caption with a "
        '<a href="https://example.com">link</a>.</p>'
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    captions = [node for node in bs.children if is_caption(node)]
    bs = prepare_ref_targets_in_captions(bs, metadata, captions)
    a = bs.find("a")
    assert a
    assert a["href"] == "https://example.com"
    assert a.string == "link"
    assert captions[0].text == "Figure {{ f-file-ref178606190 }}: Caption with a link."
    target = metadata.get_target("f-file-ref178606190")
    assert target.text == "2"
    assert len(metadata.substitutions) == 1
    assert metadata.substitutions[0]["was"] == "2"
    assert metadata.substitutions[0]["placeholder"] == "f-file-ref178606190"


# targets and refs in footnotes


def test_ref_and_target_from_footnote():
    sample_html = (
        '<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup>'
        '<ol><li id="footnote-1">'
        "<p>"
        " Standard footnote without links."
        ' <a href="#footnote-ref-1">↑</a>'
        "</p>"
        "</li></ol>"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    metadata = DocumentMetadata(KeyPath("./tmp/sth/file.docx"))
    references = []
    footnotes = []
    classifiers = [
        (is_reference, references),
        (is_footnote, footnotes),
    ]
    for node in bs.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    bs = prepare_ref_targets_in_footnotes(bs, metadata, footnotes)
    bs = prepare_references(bs, metadata, references)
    sup = bs.find("sup")
    assert sup.a.text == r"[fn-file-1]"
    assert sup.a["href"] == "#footnote-fn-file-1"
    assert sup.a["id"] == "footnote-ref-fn-file-1"
    li = bs.find("li")
    assert li["id"] == "footnote-fn-file-1"
    a = li.find("a")
    assert a["href"] == "#footnote-ref-fn-file-1"
    # not added to refs nor targets
    assert len(metadata.refs) == 0
    assert len(metadata.targets) == 0


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
    )
    assert link.make_text(bs.a.text, target) == r"Figure {{ f-ref177042490 }}"
    assert link.make_destination() == "#f-ref177042490"
    assert link.text_to_replace == "1"
    assert link.unique_id == "f-ref177042490"


def test_markownify_anchor_if_is_inner_reference__simple_a_tag():
    sample_html = '<a href="#_Ref177042491">Figure 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    target = TargetDatapoint(
        pk="_Ref177042491",
        html='<data value=" SEQ Figure \\* ARABIC ">2</data>',
        text="2",
    )
    assert link.make_text(bs.a.text, target) == r"Figure {{ f-ref177042491 }}"
    assert link.make_destination() == "#f-ref177042491"
    assert link.text_to_replace == "2"
    assert link.unique_id == "f-ref177042491"


def test_markownify_anchor_if_is_cross_file_reference():
    sample_html = '<a href="filename.docx#h-target">see Chapter 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == r"see Chapter {{ filename.docx#f-h-target }}"
    assert link.make_destination() == "./filename.md#f-h-target"
    assert link.text_to_replace == "2"
    assert link.unique_id == "filename.docx#f-h-target"


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
