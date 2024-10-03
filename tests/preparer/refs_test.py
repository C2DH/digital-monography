import bs4
import re

from src.preparer.refs import add_id_to_captions_without_bookmarks


HTML_STR = f"""\
<p class="dgt-mon-caption">Figure 1: No bold.</p>
<p class="dgt-mon-caption"><strong>Figure 2:</strong> Bold, but <i>no</i> bookmark.</p>
<p class="dgt-mon-caption"><strong>Figure 3: </strong>Also bold, but space in a different place. No bookmark.</p>
<p class="dgt-mon-caption"><a id="_Ref178606189"></a><strong>Figure 4:</strong> A bookmark.</p>
<!-- Duplicated anchor tag -->
<p class="dgt-mon-caption"><a id="_Ref178606187"></a><a id="_Ref178606188"></a><strong>Figure 5:</strong> Duplicated bookmarks.</p>
<!-- Captions with links -->
<p class="dgt-mon-caption"><strong>Figure 6: </strong>Caption with a <a href="example.com">link</a> but no bookmark.</p>
<p class="dgt-mon-caption"><a id="_Ref178606189"></a><strong>Figure 7:</strong> Caption with a <a href="example.com">link</a> and a bookmark.</p>
"""


class TestManagingReferences:
    @classmethod
    def setup_class(cls):
        cls.html_soup = bs4.BeautifulSoup(HTML_STR, "html.parser")
        cls.html_soup = add_id_to_captions_without_bookmarks(cls.html_soup)
        cls.html_soup_str = str(cls.html_soup)

    def test_id_was_added_to_unreferenced(self):
        for child in self.html_soup.children:
            if type(child) == bs4.element.Tag:
                anchors = child.find_all("a", id=True)
                assert len(anchors) > 0
                for a in anchors:
                    assert a["id"]
                    assert a["id"].startswith("_Ref") or a["id"].startswith("_Unref")

    def test_if_caption_content_was_injected_to_anchor(self):
        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}">Figure 1: No bold.</a></p>'
        assert (
            re.match(pattern, self.html_soup_str) is not None
        ), "Injecting _Unref anchor tag failed."
        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}"><strong>Figure 2:</strong> Bold, but <i>no</i> bookmark\.</a></p>'
        assert (
            re.search(pattern, self.html_soup_str) is not None
        ), "Injecting _Unref anchor tag to complex caption failed."

        assert (
            '<p class="dgt-mon-caption"><a id="_Ref178606187"><a id="_Ref178606188"></a><strong>Figure 5:</strong> Duplicated bookmarks.</a></p>'
            in self.html_soup_str
        )
        pattern = r'<p class="dgt-mon-caption"><a id="_Unref[0-9]{9}"><strong>Figure 6: </strong>Caption with a <a href="example.com">link</a> but no bookmark.</a></p>'
        assert (
            re.search(pattern, self.html_soup_str) is not None
        ), "Injecting _Unref anchor tag to a caption with a link failed."
        assert (
            '<p class="dgt-mon-caption"><a id="_Ref178606189"><strong>Figure 7:</strong> Caption with a <a href="example.com">link</a> and a bookmark.</a></p>'
            in self.html_soup_str
        )
