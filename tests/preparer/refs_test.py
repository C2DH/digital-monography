import bs4
import re

from src.preparer.refs import handle_targets_in_caption, handle_refs, LinkMystifier
from src.preparer.metadata import DocumentMetadata, TargetDatapoint


CAPTIONS_HTML = rf"""
<p class="dgt-mon-caption">Figure <data value=" SEQ Figure \* ARABIC ">1</data>: No bold.</p>
<p class="dgt-mon-caption"><strong>Figure <data value=" SEQ Figure \* ARABIC ">2</data>:</strong> Bold, but <i>no</i> bookmark.</p>
<p class="dgt-mon-caption"><strong>Figure <data value=" SEQ Figure \* ARABIC ">3</data>: </strong>Also bold, but space in a different place. No bookmark.</p>
<p class="dgt-mon-caption"><a id="_Ref178606189"></a><strong>Figure <data value=" SEQ Figure \* ROMAN ">IV</data>:</strong> A bookmark.</p>
<!-- Duplicated anchor tag -->
<p class="dgt-mon-caption"><a id="_Ref178606187"></a><a id="_Ref178606188"></a><strong>Figure <data value=" STYLEREF 1 \s ">5</data>.<data value=" SEQ Equation \* ALPHABETIC \s 1 ">A</data>:</strong> Complex numbering + duplicated bookmarks.</p>
<p class="dgt-mon-caption"><a id="_Ref178606189"></a><strong>Figure <data value=" STYLEREF 1 \s ">5</data><i>.</i><data value=" SEQ Equation \* ALPHABETIC \s 1 ">B</data>:</strong> Complex numbering with separator.</p>
<!-- Captions with links -->
<p class="dgt-mon-caption"><strong>Figure <data value=" SEQ Figure \* ARABIC ">6</data>: </strong>Caption with a <a href="example.com">link</a> but no bookmark.</p>
<p class="dgt-mon-caption"><a id="_Ref178606190"></a><strong>Figure <data value=" SEQ Figure \* ARABIC ">7</data>:</strong> Caption with a <a href="example.com">link</a> and a bookmark.</p>
"""


class TestManagingTargetsInCaptions:
    @classmethod
    def setup_class(cls):
        cls.html_soup = bs4.BeautifulSoup(CAPTIONS_HTML, "html.parser")
        cls.metadata = DocumentMetadata()
        cls.html_soup = handle_targets_in_caption(cls.html_soup, cls.metadata)
        cls.html_str = str(cls.html_soup)

    def test_id_was_added_to_unreferenced(self):
        for child in self.html_soup.children:
            if type(child) == bs4.element.Tag:
                anchors = child.find_all("a", id=True)
                assert len(anchors) > 0
                for a in anchors:
                    assert a["id"]
                    assert a["id"].startswith("_Ref") or a["id"].startswith("_Unref")

    def test_if_unref_anchor_tag_to_caption(self):
        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}">Figure ({{ _Unref[0-9]{9} }}): No bold.</a></p>'
        assert (
            re.search(pattern, self.html_str) is not None
        ), "Injecting _Unref anchor tag failed."

        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}"><strong>Figure ({{ _Unref[0-9]{9} }}):</strong> Bold, but <i>no</i> bookmark\.</a></p>'
        assert (
            re.search(pattern, self.html_str) is not None
        ), "Injecting _Unref anchor tag to complex caption failed."

        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}"><strong>Figure ({{ _Unref[0-9]{9} }}): </strong>Caption with a <a href="example.com">link</a> but no bookmark.</a></p>'
        assert (
            re.search(pattern, self.html_str) is not None
        ), "Injecting _Unref anchor tag to a caption with a link failed."

    def test_if_caption_content_was_injected_to_anchor(self):
        assert (
            '<p class="dgt-mon-caption"><a id="_Ref178606187"><a id="_Ref178606188"></a><strong>Figure {{ _Ref178606187 }}:</strong> Complex numbering + duplicated bookmarks.</a></p>'
            in self.html_str
        ), "Handling duplicated anchor tag OR handling complex numbering failed."

        assert (
            '<p class="dgt-mon-caption"><a id="_Ref178606189"><strong>Figure {{ _Ref178606189 }}:</strong> Complex numbering with separator.</a></p>'
            in self.html_str
        ), "Handling complex numbering failed."

        assert (
            '<p class="dgt-mon-caption"><a id="_Ref178606190"><strong>Figure {{ _Ref178606190 }}:</strong> Caption with a <a href="example.com">link</a> and a bookmark.</a></p>'
            in self.html_str
        ), "Handling a caption with a link and a bookmark failed."


# LinkMystifier attributes


def test_is_external_url():
    sp = LinkMystifier("https://c2dh.uni.lu/")
    assert sp.uri == "https://c2dh.uni.lu/"
    assert sp.scheme == "https"
    assert sp.netloc == "c2dh.uni.lu"
    assert sp.path == "/"
    assert sp.query == ""
    assert sp.fragment == ""
    assert sp.is_external_url() == True
    assert sp.is_cross_file_reference() == False
    assert sp.is_inner_reference() == False


def test_is_external_url_with_path():
    sp = LinkMystifier("http://c2dh.uni.lu/people/")
    assert sp.uri == "http://c2dh.uni.lu/people/"
    assert sp.scheme == "http"
    assert sp.netloc == "c2dh.uni.lu"
    assert sp.path == "/people/"
    assert sp.query == ""
    assert sp.fragment == ""
    assert sp.is_external_url() == True
    assert sp.is_cross_file_reference() == False
    assert sp.is_inner_reference() == False


def test_is_inner_reference():
    sp = LinkMystifier("#_Ref177042490")
    assert sp.uri == "#_Ref177042490"
    assert sp.scheme == ""
    assert sp.netloc == ""
    assert sp.path == ""
    assert sp.query == ""
    assert sp.fragment == "_Ref177042490"
    assert sp.is_external_url() == False
    assert sp.is_cross_file_reference() == False
    assert sp.is_inner_reference() == True


def test_is_cross_file_reference():
    sp = LinkMystifier("filename.docx#heading1")
    assert sp.scheme == ""
    assert sp.netloc == ""
    assert sp.path == "filename.docx"
    assert sp.query == ""
    assert sp.fragment == "heading1"
    assert sp.is_external_url() == False
    assert sp.is_cross_file_reference() == True
    assert sp.is_inner_reference() == False


def test_is_not_external_url_nor_cross_file_ref_nor_inner_ref():
    sp = LinkMystifier("example.com")
    assert sp.is_external_url() == False
    assert sp.is_cross_file_reference() == False
    assert sp.is_inner_reference() == False


def test_myst_md_target__is_cross_file_reference():
    sp = LinkMystifier("filename.docx#heading1")
    assert sp.destination == "./filename.md#heading1"


# LinkMystifier.markdownify()


def test_markownify_anchor_if_is_external_url():
    sample_html = '<a href="https://c2dh.uni.lu">the website</a>'
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    assert link.markdownify(a_tag.text) == "[the website](https://c2dh.uni.lu)"


def test_markownify_anchor_if_is_external_url_with_path():
    sample_html = '<a href="http://c2dh.uni.lu/people/">a website</a>'
    expected_html = "[a website](http://c2dh.uni.lu/people/)"
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    assert link.markdownify(a_tag.text) == expected_html


def test_markownify_anchor_if_is_inner_reference__complex_a_tag():
    sample_html = '<a href="#_Ref177042490">Figure <strong>1</strong></a>'
    expected_html = r"[Figure {{ _Ref177042490 }}](#_Ref177042490)"
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    target = TargetDatapoint(
        full_id="_Ref177042490",
        html='<data value=" SEQ Figure \\* ARABIC ">1</data>',
        text="1",
    )
    assert link.markdownify(a_tag.text, target) == expected_html


def test_markownify_anchor_if_is_inner_reference__simple_a_tag():
    sample_html = '<a href="#_Ref177042491">Figure 2</a>'
    expected_html = r"[Figure {{ _Ref177042491 }}](#_Ref177042491)"
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    target = TargetDatapoint(
        full_id="_Ref177042491",
        html='<data value=" SEQ Figure \\* ARABIC ">2</data>',
        text="2",
    )
    assert link.markdownify(a_tag.text, target) == expected_html


def test_markownify_anchor_if_is_cross_file_reference():
    sample_html = '<a href="filename.docx#h-target">see Chapter 2</a>'
    expected_html = (
        r"[see Chapter {{ filename.docx#h-target }}](./filename.md#h-target)"
    )
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    assert link.markdownify(a_tag.text) == expected_html


def test_markownify_anchor_if_is_cross_file_reference__nothing_to_replace():
    sample_html = '<a href="filename.docx#h-target">see heading in other file</a>'
    expected_html = r"[see heading in other file](./filename.md#h-target)"
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    assert link.markdownify(a_tag.text) == expected_html


def test_markownify_anchor_if_is_not_external_url_nor_cross_file_ref_nor_inner_ref():
    sample_html = '<a href="example.com">the website</a>'
    expected_html = r"[the website](example.com)"
    bs = bs4.BeautifulSoup(sample_html, "html.parser")
    a_tag = bs.a
    link = LinkMystifier(a_tag["href"])
    assert link.markdownify(a_tag.text) == expected_html
