import bs4
import mammoth
import pathlib

from src.preparer.citations import add_bibliography, prepare_citations, is_citation
from src.preparer.html2md import convert_to_md
from src.preparer.metadata import DocumentMetadata


class TestHtml2MdFootnotes:
    fp = pathlib.Path("tests") / "_fixtures" / "citation_in_footnotes.docx"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f)
        cls.soup = bs4.BeautifulSoup(result.value, "html.parser")
        metadata = DocumentMetadata()
        citations = []
        for node in cls.soup.descendants:
            if is_citation(node):
                citations.append(node)
        cls.soup, bibliography = prepare_citations(cls.soup, metadata, citations)
        cls.soup = add_bibliography(cls.soup, bibliography)
        cls.md = convert_to_md(cls.soup, metadata)

    def test_footnote_ref_properly_converted_to_myst_syntax(self):
        expected_md_start = "Claim A[^footnote-ref-1]. Claim B[^footnote-ref-2]."
        assert self.md.startswith(expected_md_start)

    def test_footnotes_properly_converted_to_myst_syntax(self):
        expected_md_includes = r"[^footnote-ref-1]:  Joe Schmoe, „Just no“, Opinions, 1, Nr. 1 (2035): 1–2."
        assert expected_md_includes in self.md

    def test_footnote_with_link_to_myst(self):
        sample_html = (
            # ref
            "<p>Claim"
            "<sup>"
            '<a href="#footnote-fn-02-a-99" id="footnote-ref-fn-02-a-99">[fn-02-a-99]</a>'
            "</sup>"
            ".</p>"
            # target
            "<ol>"
            '<li id="footnote-fn-02-a-99">'
            "<p>"
            ' <a href="http://www.example.com/">Link to an external website</a>'
            ' <a href="#footnote-ref-fn-02-a-99">↑</a>'
            "</p>"
            "</li>"
            "</ol>"
        )
        expected_md = (
            "Claim[^footnote-ref-fn-02-a-99].\n\n"
            "[^footnote-ref-fn-02-a-99]:  [Link to an external website](http://www.example.com/) \n\n"
        )
        html_soup = bs4.BeautifulSoup(sample_html, "html.parser")
        metadata = DocumentMetadata()
        md = convert_to_md(html_soup, metadata)
        assert md == expected_md


def test_heading_targets_markdownification():
    html = "<pre>(heading-target)=</pre><h1>Title</h1>"
    html_soup = bs4.BeautifulSoup(html, "html.parser")
    metadata = DocumentMetadata()
    md = convert_to_md(html_soup, metadata)
    assert md == "\n\n(heading-target)=\n# Title\n\n"


class TestHtml2MdGreedy:
    fp = pathlib.Path("tests") / "_fixtures" / "greedy.docx"

    @classmethod
    def setup_class(cls):
        style_mappings = """
        p[style-name='Quote'] => blockquote:fresh
        p[style-name='Caption'] => p.dgt-mon-caption:fresh
        """
        with open(cls.fp, "rb") as f:
            result = mammoth.convert_to_html(f, style_map=style_mappings)
        cls.html_soup = bs4.BeautifulSoup(result.value, "html.parser")
        cls.metadata = DocumentMetadata()
        cls.md = convert_to_md(cls.html_soup, cls.metadata)

    def test_two_new_lines_after_blockquote_element(self):
        assert "a\n\n> b\n\nc\n\n" in self.md
        #               ^^^^ # must be 2 \n to stop swallowing of the next el
