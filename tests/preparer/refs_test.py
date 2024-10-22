import bs4

from src.preparer.refs import (
    is_caption,
    is_header,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
    LinkMystifier,
)
from src.preparer.metadata import DocumentMetadata, TargetDatapoint
from src.preparer.keys import KeyPath

# targets in headers


# def test_testing():
#     HEADERS_HTML = """\
# <h1></a>Chapter title</h1>
# <h2><a id="_Heading">Heading</h2>
# <p>A <a href="#_Heading">link</a>.</p>
# <p>B <a href="other_file.docx#_Heading">link</a>.</p>
# """


def test_targets_in_headers__heading_reference_targets():
    sample_html = '<h1><a id="_Heading">XXX</h1>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_id(bs.h1.a["id"])
    assert link.mystify_target() == "(_Heading)="
    assert link.make_destination() == "#_Heading"


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
    assert pres[0].text == "(file___Heading)="
    assert pres[1].text == "(file__heading_2)="
    assert pres[2].text == "(file__heading_3)="
    assert str(bs).startswith(
        "<pre>(file___Heading)=</pre>"
        "<pre>(file__heading_2)=</pre>"
        "<h1>Heading</h1>"
        "<h2>Heading level 2</h2>"
        "<pre>(file__heading_3)=</pre>"
        "<h3>Heading level 3</h3>"
    )


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
    assert pre.text == "(file___Ref178606189)="
    assert pre.find_next_sibling() == captions[0]
    target = metadata.get_target("file___Ref178606189")
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
    assert pres[0].text == "(file___Ref178606187)="
    assert pres[1].text == "(file___Ref178606188)="
    assert str(bs) == (
        "<pre>(file___Ref178606187)=</pre>"
        "<pre>(file___Ref178606188)=</pre>"
        '<p class="dgt-mon-caption">'
        "<strong>Figure {{ file___Ref178606187 }}:</strong>"
        " Duplicated bookmarks.</p>"
    )
    target = metadata.get_target("file___Ref178606187")
    assert target.text == "3"
    target = metadata.get_target("file___Ref178606188")
    assert target.text == "3"


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
        == "Figure {{ file___Ref178606189 }}: Complex numbering with separator."
    )
    target = metadata.get_target("file___Ref178606189")
    assert target.text == "5.B"


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
    assert captions[0].text == "Figure {{ file___Ref178606189 }}: Roman numbering."
    target = metadata.get_target("file___Ref178606189")
    assert target.text == "IV"


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
    assert captions[0].text == "Figure {{ file___Ref178606190 }}: Caption with a link."
    target = metadata.get_target("file___Ref178606190")
    assert target.text == "2"


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
    assert link.fragment == "_Ref177042490"
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
    assert link.fragment == "h-target"
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
    assert link.make_text(bs.a.text, target) == r"Figure {{ _Ref177042490 }}"
    assert link.make_destination() == "#_Ref177042490"


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
    assert link.make_text(bs.a.text, target) == r"Figure {{ _Ref177042491 }}"
    assert link.make_destination() == "#_Ref177042491"


def test_markownify_anchor_if_is_cross_file_reference():
    sample_html = '<a href="filename.docx#h-target">see Chapter 2</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == r"see Chapter {{ filename.docx#h-target }}"
    assert link.make_destination() == "./filename.md#h-target"


def test_markownify_anchor_if_is_cross_file_reference__nothing_to_replace():
    sample_html = '<a href="filename.docx#h-target">see heading in other file</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "see heading in other file"
    assert link.make_destination() == "./filename.md#h-target"


def test_markownify_anchor_if_is_not_external_url_nor_cross_file_ref_nor_inner_ref():
    sample_html = '<a href="example.com">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    link = LinkMystifier()
    link.set_from_href(bs.a["href"])
    assert link.make_text(bs.a.text) == "the website"
    assert link.make_destination() == "example.com"
