import bs4
import mammoth
import pytest

from src._common.state import DocumentState
from src._common.models import CitationGroup, CitationItem
from src._common.keys import KeyPath
from src.preparer.citations import add_bibliography, prepare_citations, is_citation


class TestCitationsFromFields:
    fp = KeyPath("tests") / "_fixtures" / "citation_in_fields.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        citations = []
        cls.docstate = DocumentState(cls.fp)
        for node in cls.html_soup.descendants:
            if is_citation(node):
                citations.append(node)
        cls.html_soup, cls.bib = prepare_citations(
            cls.html_soup, cls.docstate, citations
        )
        cls.html_soup = add_bibliography(cls.html_soup, cls.bib)

    def test_extract_citations_finds_all_citations(self):
        assert self.docstate.len("citation_groups") == 1
        assert self.docstate.len("citation_items") == 1

    def test_citation_groups_extracted(self):
        group = self.docstate.get("citation_groups", "u4qVPMeE", "id")
        assert isinstance(
            group, CitationGroup
        ), "Expected to find CitationGroup instance"
        assert group.plainCitation == "(see Ce 2010, Abb. 13 for examples)"

    def test_citation_items_extracted(self):
        item = self.docstate.get("citation_items", 43, "id")
        assert isinstance(item, CitationItem), "Expected to find CitationItem instance"
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
    fp = KeyPath("tests") / "_fixtures" / "citation_in_footnotes.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        citations = []
        cls.docstate = DocumentState(cls.fp)
        for node in cls.html_soup.descendants:
            if is_citation(node):
                citations.append(node)
        cls.html_soup, cls.bib = prepare_citations(
            cls.html_soup, cls.docstate, citations
        )
        cls.html_soup = add_bibliography(cls.html_soup, cls.bib)

    def test_extract_citations_finds_all_2_citations(self):
        assert self.docstate.len("citation_groups") == 2
        assert self.docstate.len("citation_items") == 3
        items = self.docstate.filter("citation_items", "a22p6p0ob48", "citationId")
        assert len(items) == 2
        assert isinstance(
            items[0], CitationItem
        ), "Expected to find CitationItem instance"
        assert isinstance(
            items[1], CitationItem
        ), "Expected to find CitationItem instance"

    @pytest.mark.parametrize(
        "group_id, plain_citation",
        [
            ("a1uqssb04e4", "Joe Schmoe, „Just no“, Opinions, 1, Nr. 1 (2035): 1–2."),
            (
                "a22p6p0ob48",
                "see Abe Ce, „I disagree“, in We all agree (Like Minded Publ, 2010), 12;",
            ),
        ],
    )
    def test_citation_groups_extracted(self, group_id: str, plain_citation: str):
        group = self.docstate.get("citation_groups", group_id, "id")
        assert isinstance(
            group, CitationGroup
        ), "Expected to find CitationGroup instance"
        assert group.plainCitation.startswith(plain_citation)

    @pytest.mark.parametrize(
        "item_id, typ, title, author_family, event_place",
        [
            (42, "article-journal", "Just no", "Schmoe", None),
            (43, "chapter", "I disagree", "Ce", None),
            (41, "book", "Zażółć gęślą jaźń", "Ce", "안돌이지돌이다래미한숨바우"),
        ],
    )
    def test_citation_items_extracted(
        self,
        item_id: int,
        typ: str,
        title: str,
        author_family: str,
        event_place: str | None,
    ):
        cit_item = self.docstate.get("citation_items", item_id, "id")
        assert isinstance(
            cit_item, CitationItem
        ), "Expected to find CitationItem instance"
        assert cit_item.itemData["type"] == typ
        assert cit_item.itemData["title"] == title
        assert cit_item.itemData["author"][0]["family"] == author_family
        if event_place is None:
            assert "event-place" not in cit_item.itemData
        else:
            assert cit_item.itemData["event-place"] == event_place

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
