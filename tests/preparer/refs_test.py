import bs4
import re

from src.preparer.refs import add_id_to_captions_without_bookmarks
from src.preparer.metadata import DocumentMetadata


HTML_STR = rf"""
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


class TestManagingReferences:
    @classmethod
    def setup_class(cls):
        cls.html_soup = bs4.BeautifulSoup(HTML_STR, "html.parser")
        print(cls.html_soup)
        print("-" * 25)
        cls.metadata = DocumentMetadata()
        cls.html_soup = add_id_to_captions_without_bookmarks(
            cls.html_soup, cls.metadata
        )
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
