import bs4
import mammoth
import pathlib

from src.preparer.citations import add_bibliography, prepare_citations, is_citation
from src.preparer.metadata import DocumentMetadata


class TestCitationsFromFields:
    fp = pathlib.Path("tests") / "_fixtures" / "citation_in_fields.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        citations = []
        cls.metadata = DocumentMetadata()
        for node in cls.html_soup.descendants:
            if is_citation(node):
                citations.append(node)
        cls.html_soup, cls.bib = prepare_citations(
            cls.html_soup, cls.metadata, citations
        )
        cls.html_soup = add_bibliography(cls.html_soup, cls.bib)

    def test_extract_citations_finds_all_citations(self):
        assert len(self.metadata.citation_groups) == 1
        assert len(self.metadata.citation_items) == 1

    def test_citation_groups_extracted(self):
        group = self.metadata.get_citation_group("u4qVPMeE")
        assert group.plainCitation == "(see Ce 2010, Abb. 13 for examples)"

    def test_citation_items_extracted(self):
        item = self.metadata.get_citation_item(43)
        assert item.itemData["title"] == "I disagree"
        assert item.itemData["container-title"] == "We all agree"
        assert item.itemData["publisher"] == "Like Minded Publ"
        assert item.itemData["author"][0]["given"] == "Abe"
        assert item.itemData["author"][0]["family"] == "Ce"
        assert item.itemData["issued"]["date-parts"][0] == ["2010", 12, 31]

    def test_citation_was_added(self):
        expected_html = (
            "<p>A claim <cite>(see Ce 2010, Abb. 13 for examples)</cite>.</p>"
        )
        assert str(self.html_soup).startswith(expected_html)

    def test_bibliography_was_added(self):
        expected_html = (
            "<div>"
            "<h2>Bibliography</h2>"
            "<ol>"
            "<li><small>Ce, A., 2010. I disagree. In "
            "<i>We all agree</i>"
            ".  Like Minded Publ. Available at: https://example.com/.</small></li>"
            "</ol>"
            "</div>"
        )
        assert str(self.html_soup).endswith(expected_html)


class TestCitationsFromFootnotes:
    fp = pathlib.Path("tests") / "_fixtures" / "citation_in_footnotes.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        citations = []
        cls.metadata = DocumentMetadata()
        for node in cls.html_soup.descendants:
            if is_citation(node):
                citations.append(node)
        cls.html_soup, cls.bib = prepare_citations(
            cls.html_soup, cls.metadata, citations
        )
        cls.html_soup = add_bibliography(cls.html_soup, cls.bib)

    def test_extract_citations_finds_all_2_citations(self):
        assert len(self.metadata.citation_groups) == 2
        assert len(self.metadata.citation_items) == 3
        items = self.metadata.filter("citation_items", "citationId", "a22p6p0ob48")
        assert len(items) == 2

    def test_citation_groups_extracted(self):
        group = self.metadata.get_citation_group("a1uqssb04e4")
        assert group.plainCitation.startswith(
            "Joe Schmoe, „Just no“, Opinions, 1, Nr. 1 (2035): 1–2."
        )
        group = self.metadata.get_citation_group("a22p6p0ob48")
        assert group.plainCitation.startswith(
            "see Abe Ce, „I disagree“, in We all agree (Like Minded Publ, 2010), 12;"
        )

    def test_citation_items_extracted(self):
        joe_schmoe = self.metadata.get_citation_item(42)
        abe_ce = self.metadata.get_citation_item(43)
        with_nonascii = self.metadata.get_citation_item(41)

        assert joe_schmoe.itemData["type"] == "article-journal"
        assert joe_schmoe.itemData["title"] == "Just no"
        assert joe_schmoe.itemData["author"][0]["family"] == "Schmoe"

        assert abe_ce.itemData["type"] == "chapter"
        assert abe_ce.itemData["title"] == "I disagree"
        assert abe_ce.itemData["author"][0]["family"] == "Ce"

        assert with_nonascii.itemData["type"] == "book"
        assert with_nonascii.itemData["title"] == "Zażółć gęślą jaźń"
        assert with_nonascii.itemData["author"][0]["family"] == "Ce"
        assert with_nonascii.itemData["event-place"] == "안돌이지돌이다래미한숨바우"

    def test_citation_was_added(self):
        expected_html_start = (
            "<p>Claim A<sup>"
            '<a href="#footnote-1" id="footnote-ref-1">[1]</a>'
            "</sup>. Claim B<sup>"
            '<a href="#footnote-2" id="footnote-ref-2">[2]</a>'
            "</sup>.</p>"
            '<ol><li id="footnote-1"><p> '
            "<cite>Joe Schmoe, „Just no“, Opinions, 1, Nr. 1 (2035): 1–2.</cite> "
            '<a href="#footnote-ref-1">↑</a>'
        )
        assert str(self.html_soup).startswith(expected_html_start)

    def test_bibliography_was_added(self):
        expected_html = (
            "<div>"
            "<h2>Bibliography</h2>"
            "<ol>"
            "<li><small>Schmoe, J., 2035. Just no. , 1(1), pp.1–2.</small></li>"
            "<li><small>Ce, A., 2010. I disagree. In <i>We all agree</i>.  Like Minded Publ.</small></li>"
            "<li><small>Ce, A., 2023. <i>Zażółć gęślą jaźń</i>, 안돌이지돌이다래미한숨바우.</small></li>"
            "</ol>"
            "</div>"
        )
        assert str(self.html_soup).endswith(expected_html)
